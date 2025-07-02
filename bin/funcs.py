from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import itertools
import re
from screeninfo import get_monitors
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import shutil
from telebot import types
from time import sleep
from typing import List
import traceback

from bin.glob import *
from bin import glob
from bin.workers import dynamic_worker


def bot_polling():
    print("Starting bot polling now")
    while True:
        try:
            print("New bot instance started")
            bot.polling(none_stop=True, interval=1, timeout=30)
        except KeyboardInterrupt:
            exit(1)
        except:
            print(traceback.format_exc())
            bot.stop_polling()
            sleep(5)


def thread_polling():
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(bot_polling)


def init_browsers():
    # сортирует мониторы по координатам
    mon_limit = int(get_item_from_config('MAIN')['mon_limit'])
    monitors = sorted(get_monitors(), key=lambda d: d.x)[:mon_limit]
    # monitors = sorted(get_monitors(), key=lambda d: d.x)
    results = []
    with ThreadPoolExecutor() as executor:
        for mon_num in range(len(monitors)):
            for win_num in range(1, 5):
                results.append(
                    executor.submit(
                        Window, mon_num + 1, win_num, monitors[mon_num]
                    )
                )
    glob.all_windows = [item.result() for item in results]


def start_browsers():
    with ThreadPoolExecutor(max_workers=len(glob.all_windows)) as executor:
        executor.map(Window.start, glob.all_windows)


def allocate_browsers():
    with ThreadPoolExecutor(max_workers=len(glob.all_windows)) as executor:
        executor.map(Window.def_allocation, glob.all_windows)


def start_bots():
    with ThreadPoolExecutor(max_workers=len(glob.all_windows)) as executor:
        try:
            futures = {
                executor.submit(dynamic_worker, win): win
                for win in itertools.islice(glob.all_windows, len(glob.all_windows))
            }
            while futures:
                done, _ = concurrent.futures.wait(
                    futures, return_when=concurrent.futures.FIRST_COMPLETED
                )
                [futures.pop(fut) for fut in done]
                for item in done:
                    refresh_win = [win for win in glob.all_windows if win.id == item.result().id][0]
                    fut = executor.submit(dynamic_worker, refresh_win)
                    futures[fut] = refresh_win
        except KeyboardInterrupt:
            print(traceback.format_exc())
            exit(1)


def set_task(call: types.CallbackQuery, action, objects: List[Window]):
    msg_kb = call.message.json['reply_markup']['inline_keyboard']
    button = [item for row in msg_kb for item in row if item['callback_data'] == call.data]
    value = '' if button[0]['text'] == 'Без фильтра' else button[0]['text']
    for win in objects:
        if action in ['clicker', 'grafana']:
            if win.task_name != action or win.filter != value:
                win.task_name, win.filter, win.new_task = action, value, True
            print(f'on win {win.id} set task {action} with filter {value}')
        if action in ['pause']:
            # для того что бы не переписывать текущую задачу и после снятия вернулся правильный worker
            win.pause = True
            print(f'on win {win.id} set {action}')
        if action in ['unpause']:
            # для того что бы не переписывать текущую задачу и при возврате вернулся правильный worker
            win.refresh_timestamp, win.button_timestamp = datetime.now(), datetime.now()
            win.pause = False
            print(f'on win {win.id} set {action}')
        if action in ['url', 'img']:
            if win.task_name != action or win.filter != call.message.text:
                win.task_name, win.filter, win.new_task = action, call.message.text, True
            print(f'on win {win.id} set {action}')
        if action in ['timeout']:
            win.timeout = int(value)
        if action in ['refresh']:
            try:
                win.driver.refresh()
            except TimeoutException:
                pass


def set_form(target_position, objects):
    for win in objects:
        if win.blocked_by:
            return
        if target_position in ['fullscreen']:
            operation_fs(win)
        if target_position in ['up', 'down', 'left', 'right']:
            operation_custom_size(win, target_position)
        if target_position in ['standard']:
            operation_home(win)
        win.position = target_position


def send_button(button_name, objects):
    try:
        for win in objects:
            body = win.driver.find_element_by_xpath('/html/body')
            body.click()
            buttons_alias = dict(
                arrowup=Keys.ARROW_UP,
                pgup=Keys.PAGE_UP,
                home=Keys.HOME,
                arrowdown=Keys.ARROW_DOWN,
                pgdn=Keys.PAGE_DOWN,
                end=Keys.END,
            )
            ActionChains(win.driver).send_keys(buttons_alias[button_name]).perform()
    except:
        pass


def go_to_url(msg, params):
    win = define_wins(params)[0]
    win.task_name, win.filter, win.new_task = 'url', msg.text, True


def operation_fs(win: Window):
    win.set_fullscreen()
    for item in glob.all_windows:
        if item.mon_num == win.mon_num and win.id != item.id:
            item.blocked_by = win.id


def operation_home(win: Window):
    for item in glob.all_windows:
        if item.id == win.id or item.blocked_by == win.id:
            item.refresh_timestamp, item.button_timestamp = datetime.now(), datetime.now()
            item.blocked_by = None
            item.def_allocation()


def operation_custom_size(win: Window, position):
    conflict_win_num = check_available_form(win.win_num, position)
    if conflict_win_num:
        conflict_win = [i for i in glob.all_windows if i.win_num == conflict_win_num and i.mon_num == win.mon_num][0]
        if conflict_win.blocked_by:
            last_block_win = [i for i in glob.all_windows if i.id == conflict_win.blocked_by][0]
            last_block_win.def_allocation()
        # меняем форму окна
        getattr(win, f"{position}_side")()
        # Блокируем окно, которое мешает
        conflict_win.blocked_by = win.id
        # снимаем блок со всех остальных
        for item in glob.all_windows:
            # на которые влияло текущее окно за исключением конфликтного
            if item.blocked_by == win.id and item.id != conflict_win.id:
                item.refresh_timestamp, item.button_timestamp = datetime.now(), datetime.now()
                item.blocked_by = None


def run_preset(preset_name):
    def set_one_window(win: Window, task):
            win.filter = task['filter']
            win.timeout = task['refresh']
            win.task_name = task['task']
            win.new_task = True
            if win.position != task['window_position']:
                print(f"{win.id} set_form {task['window_position']}")
                set_form(task['window_position'], [win])

    tasks = get_clicker_cfg_table(preset_name)
    with ThreadPoolExecutor(max_workers=len(glob.all_windows)) as executor:
        for item in tasks:
            for obj in glob.all_windows:
                if int(item['window_name']) == obj.id:
                    executor.submit(set_one_window, obj, item)


def define_wins(params):
    mon_n, win_n = params.split('/')[:2]
    if mon_n != '0' and win_n != '0':
        return [i for i in glob.all_windows if i.win_num == int(win_n) and i.mon_num == int(mon_n)]
    elif win_n == '0' and mon_n == '0':
        return glob.all_windows
    elif win_n == '0':
        return [i for i in glob.all_windows if i.mon_num == int(mon_n)]


def check_available_form(win_num, side):
    conflict_dict = dict(up=[1, 2], down=[4, 3],  left=[4, 1], right=[3, 2])
    conf_arr = conflict_dict.get(side, None)
    if conf_arr:
        conf_arr.remove(win_num)
        return conf_arr[0]
    return False


def load_update(msg: types.Message):
    load_msg = bot.send_message(msg.chat.id, f'Start download update file {msg.document.file_name}')
    try:
        try:
            os.makedirs('received') if not os.path.exists('received') else None
        except:
            pass
        file = bot.download_file(bot.get_file(msg.document.file_id).file_path)
        with open(os.path.join('received', msg.document.file_name), 'wb') as new_file:
            new_file.write(file)
        bot.edit_message_text(chat_id=load_msg.chat.id,
                              message_id=load_msg.id,
                              text=f'Update file {msg.document.file_name} loaded.')
        return msg.document.file_name
    except apihelper.ApiTelegramException:
        bot.edit_message_text(chat_id=load_msg.chat.id,
                              message_id=load_msg.id,
                              text=f'File {msg.document.file_name} file too big')
    except:
        bot.edit_message_text(chat_id=load_msg.chat.id,
                              message_id=load_msg.id,
                              text=f'File {msg.document.file_name} not loaded. Check logs')
        print(traceback.format_exc())


def update_submodule(msg: types.Message):
    file_name = load_update(msg)
    shutil.move(os.path.join('received', file_name), file_name)
    bot.send_message(msg.chat.id, 'File loaded')


def send_report(msg: types.Message):
    nums = {1: '1️⃣', 2: '2️⃣', 3: '3️⃣', 4: '4️⃣', 5: '5️⃣'}
    url_re = 'https?://(.+/?\.?)*'
    text = ''
    for win in glob.all_windows:
        fields = [
            dict(name='Task', val=win.task_name),
            dict(name='Blocked', val=win.blocked_by),
            dict(name='Place', val=win.position),
            dict(name='Specify', val=win.filter),
        ]
        new_block = f"{'='*8}" \
                    f" {nums.get(win.mon_num, win.mon_num)}{nums.get(win.win_num, win.win_num)} " \
                    f"{'='*9}\n"
        for f in fields:
            if f['val']:
                #  дальше логика для скрытия URL
                name_part = f"{f['name']}:"
                name_len = len(name_part)
                val_part = f"{f['val']}"
                val_len = len(val_part)
                if re.match(url_re, str(f['val'])):
                    # смайлик занимает только 2 символа
                    val_part = f"""</pre>\n{f['val']}<pre>"""
                    val_len = 0
                all_symbols_len = name_len + val_len
                dot_part = '.'*(21 - all_symbols_len)
                new_block += f"<pre>{name_part} {dot_part} {val_part}</pre>\n"
        if len(text + new_block) > 4000:
            bot.send_message(msg.chat.id, text)
            text = new_block
        else:
            text += new_block
    if text:
        bot.send_message(msg.chat.id, text)


def run_modules():
    try:
        modules = ['clicker_win_numerate.exe']
        for i in modules:
            os.system(f"taskkill /F /T /IM {i}")
            os.spawnl(os.P_NOWAIT, i, i)
    except:
        print("Запустите модули руками")


def get_info(call: types.CallbackQuery):
    action = call.data.split('_')[2]
    items = define_wins(call.data.split('_')[3])
    if action == 'url':
        for win in items:
            glob.bot.send_message(call.message.chat.id, get_url(win))


def get_url(win: Window):
    return win.driver.current_url


if __name__ == '__main__':
    pass
