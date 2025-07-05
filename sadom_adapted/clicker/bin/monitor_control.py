from telebot import types
from screeninfo import get_monitors
from clicker.bin.glob import bot
import threading


def create_monitor_buttons(user_id):
    """Генерация кнопок выбора монитора"""
    monitors = get_monitors()
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    # Кнопки для каждого монитора
    for i, monitor in enumerate(monitors[:2]):  # Ограничим 2 мониторами для теста
        keyboard.add(types.InlineKeyboardButton(
            text=f"Монитор {i + 1}",
            callback_data=f"mon_{user_id}_{i + 1}"
        ))

    # Кнопка для всех мониторов
    keyboard.add(types.InlineKeyboardButton(
        text="Все мониторы",
        callback_data=f"mon_{user_id}_all"
    ))

    return keyboard


def handle_monitor_selection(call):
    """Обработка выбора монитора"""
    try:
        data = call.data.split('_')
        user_id = data[1]
        monitor_num = data[2]

        # Проверка пользователя
        if str(call.from_user.id) != user_id:
            return

        # Немедленный ответ
        bot.answer_callback_query(call.id)

        # Действия в отдельном потоке
        threading.Thread(target=process_monitor_selection, args=(call, monitor_num)).start()

    except Exception as e:
        print(f"Monitor selection error: {e}")
        bot.answer_callback_query(call.id, "Ошибка выбора монитора")


def process_monitor_selection(call, monitor_num):
    """Фоновая обработка выбора"""
    try:
        if monitor_num == 'all':
            message = "Работаю со всеми мониторами..."
            # Ваш код для всех мониторов
        else:
            message = f"Работаю с монитором {monitor_num}"
            # Ваш код для конкретного монитора

        bot.edit_message_text(
            message,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
    except Exception as e:
        print(f"Monitor processing error: {e}")