# работает только на стенде т.к. нужна версия chrome 100.0.4896.88 и соответствующий chromedriver
# версия selenium selenium==3.14.1
# pyinstaller -F --upx-exclude "vcruntime140.dll" --onefile sadom_adapted.py


import os.path
import signal

from telebot.apihelper import ApiTelegramException
from bin.chating_old import control_chating, start_image_url_chating
from bin.commands import *
from bin.funcs import *
from bin.glob import *


def call_check(call: types.CallbackQuery, call_type):
    is_stage = call.data.split('_')[1] in call_type
    is_same_user = call.data.split('_')[0] == str(call.from_user.id)
    return is_stage and is_same_user and check_chat(call.message.chat.id)


def check_chat(chat_id):
    return str(chat_id) in ['471516369', '-1002123720807']


def like_url(msg: types.Message):
    is_url = False
    if re.match(r'https?://(.+/?\.?)*', msg.text):
        is_url = True
    return is_url and check_chat(msg.chat.id)


def check_doc(msg: types.Message):
    is_img = msg.document.mime_type.startswith('image/')
    return is_img and check_chat(msg.chat.id)


def is_update(msg: types.Message):
    is_7zip = ".7z" in msg.document.file_name
    return is_7zip and check_chat(msg.chat.id)


@bot.message_handler(content_types=['photo'], func=lambda x: check_chat(x.chat.id))
@bot.message_handler(content_types=['document'], func=lambda x: check_doc(x))
def photo_handler(msg: types.Message):
    os.makedirs('img') if not os.path.exists('img') else None
    file_id = msg.document.file_id if msg.document else msg.photo[-1].file_id
    file_ext = msg.document.mime_type.split("/")[1] if msg.document else 'jpg'
    file = bot.download_file(bot.get_file(file_id).file_path)
    file_name = datetime.now().strftime(f'%d_%m_%Y_%H_%M_%S.{file_ext}')
    with open(os.path.join('img', file_name), 'wb') as new_file:
        new_file.write(file)
    abs_path = os.path.abspath(os.path.join('img', file_name))
    start_image_url_chating(msg, 'img', abs_path)


@bot.message_handler(content_types=['text'], func=lambda msg: like_url(msg))
def url_handler(msg):
    print('url_handler')
    if like_url(msg):
        start_image_url_chating(msg, 'url', msg.text)


'''@bot.message_handler(content_types=['document'], func=lambda x: is_update(x))
def download_update(msg: types.Message):
    load_update(msg)'''

'''@bot.message_handler(commands=['update_module'], func=lambda x: check_chat(x.chat.id))
def module_updater(msg: types.Message):
    wait_msg = bot.send_message(msg.chat.id, 'Wait file')
    bot.register_next_step_handler(wait_msg, update_submodule)'''

#========Заглушки========
@bot.message_handler(commands=['update_module'])
def module_updater(msg: types.Message):
    pass

@bot.message_handler(content_types=['document'], func=lambda x: is_update(x))
def download_update(msg: types.Message):
    pass
#========================

@bot.message_handler(commands=[item.__name__ for item in commands_list], func=lambda x: check_chat(x.chat.id))
def command_handler(msg):
    command_name = msg.text[1:].split('@')[0]
    globals()[command_name](msg)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    print(f"Получен callback: {call.data}")
    try:
        bot.answer_callback_query(call.id)
        if call.data.endswith('_close'):
            bot.delete_message(call.message.chat.id, call.message.id)
        else:
            control_chating(call.message.chat.id, call.from_user.id, call)
    except Exception as e:
        print(f"Ошибка обработки callback: {e}")

@bot.callback_query_handler(func=lambda call: call_check(call, ['control']))
def remote_control(call):
    control_chating(call.message.chat.id, call.from_user.id, msg_id=call.message.id, call=call)


@bot.callback_query_handler(func=lambda call: call_check(call, ['get']))
def get_call_handler(call):
    get_info(call)


@bot.callback_query_handler(func=lambda call: call_check(call, ['preset']))
def preset_callback(call):
    msg_kb = call.message.json['reply_markup']['inline_keyboard']
    preset_name = [item for row in msg_kb for item in row if item['callback_data'] == call.data][0]['text']
    run_preset(preset_name)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call_check(call, ['set', 'form', 'button']))
def set_task_callback(call):
    print(call.data)
    type_action = call.data.split('_')[1]
    action = call.data.split('_')[2]
    items = define_wins(call.data.split('_')[3])
    if type_action == 'set':
        set_task(call, action, items)
    elif type_action == 'form':
        set_form(action, items)
    elif type_action == 'button':
        send_button(action, items)
    else:
        print(call.data)
    try:
        bot.answer_callback_query(call.id)
    except ApiTelegramException:
        pass


@bot.callback_query_handler(func=lambda call: call_check(call, 'gui'))
def gui_callback(call):
    print(call.data)
    attrs = [f"{win.id}|{win.driver.get_window_position()['x']}|{win.driver.get_window_position()['y']}"
             for win in glob.all_windows if win.online]
    with open('clicker_win_numerate_conf.txt', 'w') as f:
        f.write(' '.join(attrs))
    try:
        bot.answer_callback_query(call.id)
    except ApiTelegramException:
        pass


@bot.callback_query_handler(func=lambda call: call_check(call, 'nothing'))
def set_task_callback(call):
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call_check(call, 'close'))
def set_task_callback(call):
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)


@bot.callback_query_handler(func=lambda call: True)
def set_task_callback(call):
    try:
        bot.answer_callback_query(call.id)
    except ApiTelegramException:
        pass


'''if __name__ == '__main__':
    run_modules()
    logger.info('set_bot_menu')
    set_bot_menu()
    logger.info('polling')
    thread_polling()
    logger.info('init_browsers')
    init_browsers()
    logger.info('start_browsers')
    start_browsers()
    logger.info('default_preset')
    run_preset('default')
    logger.info('start_bots')
    start_bots()'''

def shutdown_handler(signum, frame):
    """Обработчик сигналов завершения"""
    print("\nПолучен сигнал завершения...")
    for window in getattr(glob, 'all_windows', []):
        try:
            window.kill()
        except:
            pass
    sys.exit(0)

# Регистрируем обработчики
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == '__main__':
    print("Запуск системы...")

    try:
        print("1. Инициализация браузеров")
        init_browsers()

        print("2. Запуск окон Chrome")
        start_browsers()

        set_bot_menu()
        thread_polling()

    except Exception as e:
        print(f"Критическая ошибка: {e}")
        shutdown_handler(None, None)
        traceback.print_exc()
