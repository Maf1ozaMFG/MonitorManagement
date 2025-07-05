import traceback

from screeninfo import get_monitors
from telebot import types

from clicker.bin.data_loader import get_clicker_filters, get_grafana_urls, get_presets
from clicker.bin.glob import *
from clicker.bin.config_parse import get_item_from_config
from clicker.bin.funcs import go_to_url, define_wins


def kb_monitors(user_id):
    mon_limit = int(get_item_from_config('MAIN')['mon_limit'])
    monitors = sorted(get_monitors(), key=lambda d: d.x)[:mon_limit]
    kb = types.InlineKeyboardMarkup()
    buttons = []
    for item in range(1, len(monitors) + 1):
        buttons.append(
            types.InlineKeyboardButton(
                text=item,
                callback_data=f"{user_id}_control_sendWins_{item}"
            )
        )
    kb.row(*buttons)
    kb.row(types.InlineKeyboardButton(
        text='Все мониторы',
        callback_data=f"{user_id}_control_sendTasksAll_0/0"))
    kb.row(types.InlineKeyboardButton(
        'Закрыть',
        callback_data=f"{user_id}_close"))
    return kb


def kb_wins(user_id, data):
    kb = types.InlineKeyboardMarkup()
    wins_num = [['1', '2'], ['4', '3']]
    for row in wins_num:
        kb_row = []
        for win in row:
            kb_row.append(
                types.InlineKeyboardButton(
                    text=win,
                    callback_data=f"{user_id}_control_action_{data}/{win}"
                )
            )
        kb.row(*kb_row)
    kb.row(types.InlineKeyboardButton('Все окна', callback_data=f"{user_id}_control_sendTasksAll_{data}/0"))
    kb.row(types.InlineKeyboardButton(
        'Закрыть',
        callback_data=f"{user_id}_close"))
    return kb


def kb_action(user_id, data):
    kb = types.InlineKeyboardMarkup()
    rows_cfg = [
        dict(text='Конфигурация окна', callback_data=f"{user_id}_control_cfg_{data}"),
        dict(text='Постановка задачи для окна', callback_data=f"{user_id}_control_sendTasks_{data}"),
        dict(text='Close', callback_data=f"{user_id}_close")
    ]
    for item in rows_cfg:
        kb.row(types.InlineKeyboardButton(**item))
    return kb


'''def kb_task_type_one_win(user_id, data):
    kb = types.InlineKeyboardMarkup()
    rows_cfg = [
        dict(text='Clicker', callback_data=f"{user_id}_control_clicker_{data}"),
        dict(text='Grafana', callback_data=f"{user_id}_control_grafana_{data}"),
        dict(text='Pause', callback_data=f"{user_id}_set_pause_{data}"),
        dict(text='Unpause', callback_data=f"{user_id}_set_unpause_{data}"),
        dict(text='Close', callback_data=f"{user_id}_close")
    ]
    for item in rows_cfg:
        kb.row(types.InlineKeyboardButton(**item))
    return kb'''

def kb_task_type_one_win(user_id, data):
    kb = types.InlineKeyboardMarkup()
    rows_cfg = [
        dict(text='URL', callback_data=f"{user_id}_control_url_{data}"),
        dict(text='Pause', callback_data=f"{user_id}_set_pause_{data}"),
        dict(text='Unpause', callback_data=f"{user_id}_set_unpause_{data}"),
        dict(text='Close', callback_data=f"{user_id}_close")
    ]
    for item in rows_cfg:
        kb.row(types.InlineKeyboardButton(**item))
    return kb


def kb_task_type_all_win(user_id, data):
    kb = types.InlineKeyboardMarkup()
    rows_cfg = [
        dict(text='Clicker', callback_data=f"{user_id}_control_clicker_{data}"),
        dict(text='Pause', callback_data=f"{user_id}_set_pause_{data}"),
        dict(text='Unpause', callback_data=f"{user_id}_set_unpause_{data}"),
        dict(text='Вернуть окна на место', callback_data=f"{user_id}_form_standard_{data}"),
        dict(text='Показать номера окон', callback_data=f"{user_id}_gui"),
        dict(text='Пресеты', callback_data=f"{user_id}_control_presets_{data}"),
        dict(text='Close', callback_data=f"{user_id}_close")
    ]
    for item in rows_cfg:
        kb.row(types.InlineKeyboardButton(**item))
    return kb


def kb_filters(user_id, data):
    filters = get_clicker_filters()
    filters = [item['incident_code'] for item in filters]
    kb_width = 4
    # разбиение чисел на массивы, равные ширине рядов
    amount = len(filters)
    rows_array = [range(amount)[i:i + kb_width] for i in range(amount)[::kb_width]]
    keyboard = win_control_kb(user_id, 'clicker', data)
    keyboard.row(
        types.InlineKeyboardButton(
            text="Без фильтра",
            callback_data=f'{user_id}_set_clicker_{data}/None'
        )
    )
    for row in rows_array:
        kb_row = []
        for item in row:
            kb_row.append(
                types.InlineKeyboardButton(
                    text=filters[item],
                    callback_data=f'{user_id}_set_clicker_{data}/{item}'
                )
            )
        keyboard.row(*kb_row)
    keyboard.row(types.InlineKeyboardButton(
        'Закрыть',
        callback_data=f"{user_id}_close"))
    return keyboard


def kb_grafana(user_id, data):
    dboards = [item['short_name'] for item in get_grafana_urls()]
    kb_width = 3
    rows_array = [range(len(dboards))[i:i + kb_width] for i in range(len(dboards))[::kb_width]]
    kb = win_control_kb(user_id, 'grafana', data)
    for row in rows_array:
        kb_row = []
        for item in row:
            kb_row.append(
                types.InlineKeyboardButton(
                    text=dboards[item],
                    callback_data=f'{user_id}_set_grafana_{data}/{item}'
                )
            )
        kb.row(*kb_row)
    kb.row(types.InlineKeyboardButton(
        'Закрыть',
        callback_data=f"{user_id}_close"))
    return kb


def no_kb(user_id, data):
    return None


def win_control_kb(user_id, stage, data):
    mon_n, win_n = data.split('/')
    kb = types.InlineKeyboardMarkup()
    # if mon_n == '0' or win_n == '0':
    #     return kb
    mon_limit = int(get_item_from_config('MAIN')['mon_limit'])
    monitors = sorted(get_monitors(), key=lambda d: d.x)[:mon_limit]
    wins_1line = [1, 2]
    wins_2line = [4, 3]
    rows_cfg = [
        [dict(
            text=f"M-{i}✅" if i == int(mon_n) else f"M-{i}",
            callback_data=f"{user_id}_control_{stage}_{0}/{win_n}"
            if i == int(mon_n) else f"{user_id}_control_{stage}_{i}/{win_n}")
            for i in range(1, len(monitors) + 1)],
        [dict(
            text=f"W-{w}✅" if w == int(win_n) else f"W-{w}",
            callback_data=f"{user_id}_control_{stage}_{mon_n}/{0}"
            if w == int(win_n) else f"{user_id}_control_{stage}_{mon_n}/{w}")
            for w in wins_1line],
        [dict(
            text=f"W-{w}✅" if w == int(win_n) else f"W-{w}",
            callback_data=f"{user_id}_control_{stage}_{mon_n}/{0}"
            if w == int(win_n) else f"{user_id}_control_{stage}_{mon_n}/{w}")
            for w in wins_2line],
    ]
    for row in rows_cfg:
        kb_row = []
        for item in row:
            kb_row.append(types.InlineKeyboardButton(**item))
        kb.row(*kb_row)
    return kb


def kb_form(user_id, data):
    kb = win_control_kb(user_id, 'cfg', data)
    rows_cfg = [
        [dict(text='Fullscreen', callback_data=f"{user_id}_form_fullscreen_{data}")],
        [
            dict(text='.', callback_data=f"{user_id}_nothing"),
            dict(text='Up', callback_data=f"{user_id}_form_up_{data}"),
            dict(text='.', callback_data=f"{user_id}_nothing")
        ],
        [
            dict(text='Left', callback_data=f"{user_id}_form_left_{data}"),
            dict(text='Standard', callback_data=f"{user_id}_form_standard_{data}"),
            dict(text='Right', callback_data=f"{user_id}_form_right_{data}")
        ],
        [
            dict(text='.', callback_data=f"{user_id}_nothing"),
            dict(text='Down', callback_data=f"{user_id}_form_down_{data}"),
            dict(text='.', callback_data=f"{user_id}_nothing")
        ],
        # [
        #     dict(text='🔼', callback_data=f"{user_id}_button_arrowup_{data}"),
        #     dict(text='PgUp', callback_data=f"{user_id}_button_pgup_{data}"),
        #     dict(text='⏫', callback_data=f"{user_id}_button_home_{data}")
        # ],
        # [
        #     dict(text='🔽', callback_data=f"{user_id}_button_arrowdown_{data}"),
        #     dict(text='PgDn', callback_data=f"{user_id}_button_pgdn_{data}"),
        #     dict(text='⏬', callback_data=f"{user_id}_button_end_{data}")
        # ],
        [dict(text='Get current url', callback_data=f"{user_id}_get_url_{data}")],
        [dict(text='Refresh time,s', callback_data=f"{user_id}_set_refresh_{data}")],
        [
            dict(text='30', callback_data=f"{user_id}_set_timeout_{data}/30"),
            dict(text='60', callback_data=f"{user_id}_set_timeout_{data}/60"),
            dict(text='120', callback_data=f"{user_id}_set_timeout_{data}/90"),
            dict(text='600', callback_data=f"{user_id}_set_timeout_{data}/600")
        ],
        [dict(text='Close', callback_data=f"{user_id}_close")]
    ]
    for row in rows_cfg:
        kb_row = []
        for item in row:
            kb_row.append(types.InlineKeyboardButton(**item))
        kb.row(*kb_row)
    return kb


def kb_presets(user_id, data):
    kb = types.InlineKeyboardMarkup()
    presets = [item['preset'] for item in get_presets()]
    for i in enumerate(presets):
        kb.row(types.InlineKeyboardButton(text=i[1], callback_data=f"{user_id}_preset_{i[0]}"))
    kb.row(types.InlineKeyboardButton('Close', callback_data=f"{user_id}_close"))
    return kb


def kb_img(user_id, data=None):
    if not data:
        data = '0/0'
    kb = win_control_kb(user_id, 'img', data)
    kb.row(types.InlineKeyboardButton('Accept', callback_data=f"{user_id}_set_img_{data}"))
    kb.row(types.InlineKeyboardButton('Close', callback_data=f"{user_id}_close"))
    return kb


def kb_url(user_id, data=None):
    if not data:
        data = '0/0'
    kb = win_control_kb(user_id, 'url', data)
    kb.row(types.InlineKeyboardButton('Accept', callback_data=f"{user_id}_set_url_{data}"))
    kb.row(types.InlineKeyboardButton('Close', callback_data=f"{user_id}_close"))
    return kb


def start_control_chating(chat_id, user_id, msg_id):
    # bot.delete_message(chat_id=chat_id, message_id=msg_id)
    bot.send_message(
        chat_id=chat_id,
        text='Выбери монитор',
        reply_markup=kb_monitors(user_id)
    )


def header_text(params):
    text = ''
    attrs = ['Монитор', 'Окно', 'Blocked by']
    values = params.split('/')
    if len(values) > 1:
        if '0' not in values:
            blocked = define_wins(params)[0].blocked_by
            if blocked:
                values.append(blocked)
    for i in range(len(values)):
        value = "Все" if values[i] == '0' else values[i]
        text += f'<pre>{attrs[i]}: {value}</pre>\n'
    return text


def control_chating(chat_id, user_id, call: types.CallbackQuery, msg_id):
    stage = call.data.split('_')[2]
    data = call.data.split('_')[3]
    stages = dict(
        sendWins=dict(
            text=f'{header_text(data)}Выбери окно',
            keyboard=kb_wins
        ),
        action=dict(
            text=f'{header_text(data)}Выбери действие',
            keyboard=kb_action
        ),
        sendTasks=dict(
            text=f'{header_text(data)}Выбери источник',
            keyboard=kb_task_type_one_win
        ),
        sendTasksAll=dict(
            text=f'{header_text(data)}Выбери действие',
            keyboard=kb_task_type_all_win,
        ),
        clicker=dict(
            text=f'{header_text(data)}Выбери фильтр',
            keyboard=kb_filters
        ),
        grafana=dict(
            text=f'{header_text(data)}Grafana',
            keyboard=kb_grafana
        ),
        customUrl=dict(
            text=f'{header_text(data)}Введите полный URL целевой страницы',
            keyboard=no_kb
        ),
        cfg=dict(
            text=f'{header_text(data)}Выберите действие',
            keyboard=kb_form
        ),
        presets=dict(
            text=f'Выберите пресет',
            keyboard=kb_presets
        ),
        url=dict(
            text=call.message.text,
            keyboard=kb_url
        ),
        img=dict(
            text=call.message.text,
            keyboard=kb_img
        )
    )
    cur_stage = stages.get(stage, None)
    if cur_stage:
        success = edit_msg(chat_id, msg_id, cur_stage['text'], cur_stage['keyboard'](user_id, data))
        if not success:
            del_msg(chat_id, msg_id)
            bot.send_message(
                chat_id=chat_id,
                text=cur_stage['text'],
                reply_markup=cur_stage['keyboard'](user_id, data)
            )
    else:
        bot.send_message(chat_id, 'Функция в разработке')


def start_image_url_chating(msg: types.Message, type, link):
    kb = kb_img(msg.from_user.id) if type == 'img' else kb_url(msg.from_user.id)
    bot.send_message(
        chat_id=msg.chat.id,
        text=link,
        reply_markup=kb
    )


def edit_msg(ch_id, msg_id, text, kb):
    try:
        bot.edit_message_text(
            chat_id=ch_id,
            message_id=msg_id,
            text=text,
            reply_markup=kb
        )
        return True
    except:
        return False


def del_msg(ch_id, msg_id):
    try:
        bot.delete_message(chat_id=ch_id, message_id=msg_id)
    except:
        pass


if __name__ == '__main__':
    pass
