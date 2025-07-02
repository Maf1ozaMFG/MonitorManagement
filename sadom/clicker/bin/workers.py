from datetime import datetime
import random
from selenium.common.exceptions import NoSuchWindowException, NoSuchElementException, InvalidSessionIdException
import traceback
from time import sleep

from bin import glob
from bin.objects import Window
from bin.db import get_tasks_table, get_grafana_urls


def dynamic_worker(win: Window):
    sleep(0.1)  # не большая задержка существенно сокращает количество выполнений
    try:
        if win.pause:
            pause_mode(win)
        elif win.blocked_by:
            offline_mode(win)
        else:
            #  разбудит если окно было в оффлайне
            awake(win)
            globals()[f"{win.task_name}_worker"](win)
    except NoSuchWindowException:
        pass
    except InvalidSessionIdException:
        pass
    except Exception:
        print(traceback.format_exc())
    finally:
        return win


def pause_mode(win: Window):
    win.set_title("PAUSED")
    sleep(1)


def offline_mode(win: Window):
    if win.online:
        win.online = False
        win.set_minimize()
    sleep(1)


def awake(win: Window):
    if not win.online:
        win.online = True
        win.def_allocation()


def clicker_worker(win: Window):
    win.auth()
    win.set_title()
    if its_refresh_time(win) or win.new_task:
        win.cur_task = choose_task(win)
        if not win.cur_task:
            return
        glob.logger.info(f'{win.id}: get_url')
        win.driver.get(win.cur_task['start_link'])
        win.refresh_timestamp, win.button_timestamp = datetime.now(), datetime.now()
        win.button_number = 0
        win.new_task = False
    if (datetime.now() - win.button_timestamp).seconds > 2:
        xpath = win.cur_task.get('xpath', None)
        if xpath:
            buttons = xpath.split(r'\\')
            if win.button_number < len(buttons):
                button_name = buttons[win.button_number]
                clicked = btn_click(win.driver, button_name)
                if clicked:
                    win.button_number += 1
                    win.button_timestamp = datetime.now()


def grafana_worker(win: Window):
    win.auth()
    win.set_title()
    if its_refresh_time(win) or win.new_task:
        win.cur_task = [item for item in get_grafana_urls() if item['short_name'] == win.filter][0]
        win.driver.get(win.cur_task['url'])
        win.refresh_timestamp = datetime.now()
        win.new_task = False


def url_worker(win: Window):
    win.auth()
    win.set_title()
    if its_refresh_time(win) or win.new_task:
        win.driver.get(win.filter)
        win.refresh_timestamp = datetime.now()
        win.new_task = False


def img_worker(win: Window):
    win.set_title("PAUSED")
    if win.driver.current_url.replace('file:///', '').replace('/', '\\') != win.filter:
        win.driver.get(win.filter)
    sleep(1)


def None_worker(win: Window):
    # на случай пустой задачи
    sleep(1)
# ========== support functions =============


def its_refresh_time(win: Window):
    return True if (datetime.now() - win.refresh_timestamp).seconds > win.timeout else False


def choose_task(win: Window):
    queue = get_tasks_table()
    if win.filter:
        queue = [item for item in queue if win.filter in item['incident_code']]
    if not queue:
        return None
    queue_filtred_by_other_wins = queue.copy()
    for item in glob.all_windows:
        if item.cur_task in queue_filtred_by_other_wins:
            queue_filtred_by_other_wins.remove(item.cur_task)
    if not queue_filtred_by_other_wins:
        print(f'{win.id} Задач не осталось , возьму повтор')
        return random.choice(queue)
    else:
        # print(f'{win.name} было {len(queue)}, осталось {len(queue_filtred_by_other_wins)}')
        return random.choice(queue_filtred_by_other_wins)


def btn_click(driver, button):
    btn = search_btn(driver, button)
    try:
        if btn:
            btn.click()
            return True
    except Exception:
        # надо накапливать ошибку, и если кнопку не удалось нажать только тогда отпралять в лог
        pass
    return False


def search_btn_by_text(driver, btn_name):
    # абсолютное равенство
    xpath = f'//*[text()="{btn_name}"]'
    xpath_spaces = f'//*[text()=" {btn_name} "]'
    try:
        return driver.find_element_by_xpath(f'{xpath} | {xpath_spaces}')
    except NoSuchElementException as e:
        pass

    btn_name = btn_name.strip()

    # если не нашли ищем кнопку которая бы содержала такой текст
    xpath = f'//*[contains(text(),"{btn_name}")]'
    try:
        return driver.find_element_by_xpath(f'{xpath}')
    except NoSuchElementException as e:
        pass


def search_complex_btn(driver, btn_name):
    # '>' в сценарии означает, что мы не можем получить кнопку только по названию
    # (например, название соответствует некликабельному элементу).
    # Структура сценария с '>':
    # {некликабельный текст, соответствующий нужной кнопке}>{название класса элемента-предка
    # (напр., строки в таблице, где находится кнопка)}>{название класса кликабельного элемента
    # (напр., чекбокса)}
    elements = btn_name.split('>')
    xpath_text = f'//*[text()="{elements[0]}"]'
    xpath_text_spaces = f'//*[text()=" {elements[0]} "]'
    xpath = f'{xpath_text} | {xpath_text_spaces}//ancestor::*[@class="{elements[1]}"]'
    try:
        return driver.find_element_by_xpath(xpath).find_element_by_class_name(elements[2])
    except NoSuchElementException as e:
        pass


def search_numbered_btn(driver, btn_name):
    # Структура {название кнопки}?{номер кнопки} используется,
    # когда есть несколько кнопок с одинаковым названием
    btn_title = btn_name.split('?')[0]
    btn_number = int(btn_name.split('?')[1])
    xpath = f'//*[text()="{btn_title}"]'
    xpath_spaces = f'//*[text()=" {btn_title} "]'
    try:
        return driver.find_elements_by_xpath(f'{xpath} | {xpath_spaces}')[btn_number]
    except NoSuchElementException as e:
        pass


def search_btn(driver, btn_name):
    if '>' in btn_name:
        btn = search_complex_btn(driver, btn_name)
    elif '?' in btn_name:
        btn = search_numbered_btn(driver, btn_name)
    else:
        btn = search_btn_by_text(driver, btn_name)
    return btn


if __name__ == '__main__':
    pass
