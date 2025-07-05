from screeninfo import get_monitors
from telebot import types
from threading import Thread

from clicker.bin.data_loader import get_presets
from clicker.bin.funcs import run_preset, send_report, init_browsers
from clicker.bin.glob import bot
import traceback


def create_preset_keyboard(user_id):
    """Создание клавиатуры с пресетами"""
    kb = types.InlineKeyboardMarkup()
    presets = get_presets() or []

    for preset in presets:
        kb.add(types.InlineKeyboardButton(
            text=preset.get('preset', 'UNKNOWN'),
            callback_data=f"{user_id}_preset_{preset['preset']}"
        ))

    kb.add(types.InlineKeyboardButton(
        text="Назад",
        callback_data=f"{user_id}_action_back"
    ))

    return kb


def create_main_keyboard(user_id):
    """Создаем сразу основное меню без выбора мониторов"""
    kb = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        ("🔄 Пресет 1", "preset_1"),
        ("🔄 Пресет 2", "preset_2"),
        ("🛑 Остановить", "stop"),
        ("📊 Статус", "report")
    ]

    for text, action in buttons:
        kb.add(types.InlineKeyboardButton(
            text=text,
            callback_data=f"{user_id}_{action}"
        ))

    return kb


def start_control_chating(chat_id, user_id):
    """Запускаем сразу основное меню"""
    try:
        bot.send_message(
            chat_id,
            "⚙️ *Управление браузерными окнами*",
            parse_mode="Markdown",
            reply_markup=create_main_keyboard(user_id)
        )
    except Exception as e:
        print(f"Ошибка запуска меню: {e}")


def create_monitor_keyboard(user_id):
    """Клавиатура выбора монитора"""
    kb = types.InlineKeyboardMarkup()

    # Добавляем кнопки для каждого монитора
    monitors = get_monitors()
    for i in range(len(monitors)):
        kb.add(types.InlineKeyboardButton(
            text=f"Монитор {i + 1}",
            callback_data=f"{user_id}_monitor_{i + 1}"
        ))

    # Кнопка "Все мониторы"
    kb.add(types.InlineKeyboardButton(
        text="Все мониторы",
        callback_data=f"{user_id}_monitor_all"
    ))

    return kb


def handle_monitor_selection(call):
    """Обработка выбора монитора"""
    try:
        user_id = call.data.split('_')[0]
        monitor_id = call.data.split('_')[-1]

        # Проверяем принадлежность вызова
        if str(call.from_user.id) != user_id:
            return

        if monitor_id == 'all':
            # Действия для всех мониторов
            print("Выбраны все мониторы")
            # Здесь должна быть ваша логика обработки
            bot.answer_callback_query(call.id, "Работаю со всеми мониторами...")
        else:
            # Действия для конкретного монитора
            print(f"Выбран монитор {monitor_id}")
            # Здесь должна быть ваша логика обработки
            bot.answer_callback_query(call.id, f"Работаю с монитором {monitor_id}...")

    except Exception as e:
        print(f"Monitor selection error: {e}")
        bot.answer_callback_query(call.id, "Ошибка выбора монитора")


@bot.callback_query_handler(func=lambda call: call.data.split('_')[1] == 'monitor')
def monitor_callback_handler(call):
    """Специальный обработчик для выбора мониторов"""
    handle_monitor_selection(call)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        bot.answer_callback_query(call.id)

        if not call.data:
            return

        parts = call.data.split('_')
        if len(parts) < 2:
            return

        user_id = parts[0]
        action = '_'.join(parts[1:])

        if str(call.from_user.id) != user_id:
            return

        if action.startswith("preset_"):
            try:
                preset_id = action.split('_')[1]
                run_preset(preset_id)
                bot.send_message(call.message.chat.id, f"🔄 Применен пресет {preset_id}")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")

        elif action == "report":
            send_report(call.message)

        elif action == "close":
            bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        print(f"Callback error: {e}")
        traceback.print_exc()


def handle_preset(call, preset_name):
    """Применение пресета в фоновом режиме"""
    try:
        msg = bot.send_message(call.message.chat.id, f"🔄 Применяю пресет *{preset_name}*...", parse_mode="Markdown")

        def apply_preset():
            try:
                run_preset(preset_name)
                bot.edit_message_text(
                    f"✅ Пресет *{preset_name}* успешно применен",
                    chat_id=msg.chat.id,
                    message_id=msg.message_id,
                    parse_mode="Markdown"
                )
            except Exception as e:
                bot.edit_message_text(
                    f"❌ Ошибка: {str(e)}",
                    chat_id=msg.chat.id,
                    message_id=msg.message_id
                )

        Thread(target=apply_preset).start()

    except Exception as e:
        print(f"Preset error: {e}")


def handle_action(call, action):
    """Обработка основных команд"""
    try:
        if action == "select_monitor":
            bot.edit_message_text(
                "Выберите монитор:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=create_monitor_keyboard(call.from_user.id)
            )
        if action == 'show_presets':
            bot.edit_message_text(
                "📁 Выберите пресет:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=create_preset_keyboard(call.from_user.id)
            )
        elif action == 'stop_monitoring':
            from clicker.bin.commands import stop_monitoring
            stop_monitoring(call.message)
        elif action == 'report':
            send_report(call.message)
        elif action == 'back':
            bot.edit_message_text(
                "⚙️ *Управление браузерными окнами*",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="Markdown",
                reply_markup=create_main_keyboard(call.from_user.id)
            )
        elif action == 'close':
            bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        print(f"Action error: {e}")
        bot.answer_callback_query(call.id, f"Ошибка: {str(e)}", show_alert=True)

def show_main_menu(call):
    """Показ главного меню"""
    try:
        bot.edit_message_text(
            "⚙️ Управление браузерными окнами",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_main_keyboard(call.from_user.id)
        )
    except Exception as e:
        print(f"Menu error: {e}")