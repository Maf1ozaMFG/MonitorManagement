from threading import Thread

from clicker.bin.glob import *
from clicker.bin import glob
from clicker.bin.funcs import init_browsers, start_browsers, run_preset, allocate_browsers, send_report
from concurrent.futures import ThreadPoolExecutor
from telebot.types import BotCommand, Message
from clicker.bin.chating import start_control_chating

import atexit

executor = ThreadPoolExecutor(max_workers=4)
atexit.register(executor.shutdown, wait=False)

'''def start_monitoring(msg):
    """Запуск системы браузеров"""
    init_browsers()
    start_browsers()
    allocate_browsers()
    run_preset('default')'''


def stop_monitoring(msg):
    """Остановка окон с обработкой сообщения"""
    try:
        status_msg = bot.send_message(msg.chat.id, "🛑 Останавливаю окна...")

        # Закрываем окна
        for window in getattr(glob, 'all_windows', []):
            if hasattr(window, 'kill'):
                window.kill()

        bot.edit_message_text(
            "✅ Все окна закрыты",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id
        )
    except Exception as e:
        print(f"Stop error: {e}")
        bot.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id
        )

'''@bot.callback_query_handler(func=lambda call: call.data.startswith('mon_'))
def monitor_callback_wrapper(call):
    handle_monitor_selection(call)

@bot.message_handler(commands=['monitors'])
def show_monitor_menu(msg):
    bot.send_message(
        msg.chat.id,
        "Выберите монитор:",
        reply_markup=create_monitor_buttons(msg.from_user.id)
    )'''

@bot.message_handler(commands=['control'])
def control(msg):
    """Обработчик команды /control"""
    try:
        start_control_chating(msg.chat.id, msg.from_user.id)
    except Exception as e:
        bot.reply_to(msg, f"Ошибка: {str(e)}")

@bot.message_handler(commands=['report'])
def report(msg):
    """Обработчик команды /report"""
    try:
        send_report(msg)
    except Exception as e:
        bot.reply_to(msg, f"Ошибка: {str(e)}")


def install_update(msg: Message):
    """Установка ранее загруженных файлов обновления"""
    install_msg = bot.send_message(msg.chat.id, 'Updating...')
    if os.path.exists('received'):
        if len(os.listdir('received')) != 0:
            os.popen(f"start updater.exe update sadom {msg.chat.id} {token}")
            return
    bot.edit_message_text(chat_id=install_msg.chat.id,
                          message_id=install_msg.id,
                          text='Updating failed. No update files')


def hard_reset(msg: Message):
    """Полный перезапуск системы"""
    bot.send_message(msg.chat.id, 'Full restart')
    os.popen(f"start updater.exe restart sadom {msg.chat.id} {token}")


def remove_update(msg: Message):
    """Удаление ранее загруженных файлов обновления"""
    delete_msg = bot.send_message(msg.chat.id, 'Delete update files...')
    if os.path.exists('received'):
        files = os.listdir('received')
        if len(files) != 0:
            map(os.remove, files)
        bot.edit_message_text(chat_id=delete_msg.chat.id,
                              message_id=delete_msg.id,
                              text=f'Deleted files: {", ".join(files)}')
        return
    bot.edit_message_text(chat_id=delete_msg.chat.id,
                          message_id=delete_msg.id,
                          text=f'Update files not found')


def set_bot_menu():
    """Корректная настройка команд меню"""
    command_desc = [
        BotCommand(command='/control', description='Пульт управления'),
        BotCommand(command='/start_monitoring', description='Запустить окна'),
        BotCommand(command='/stop_monitoring', description='Остановить окна'),
        BotCommand(command='/report', description='Статус окон'),
        BotCommand(command='/preset', description='Сменить пресет')
    ]

    try:
        bot.set_my_commands(command_desc)
        print("Меню бота успешно настроено")
    except Exception as e:
        print(f"Ошибка настройки меню: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        # Обязательный ответ Telegram
        bot.answer_callback_query(call.id)

        if not call.data:
            return

        user_id, action = call.data.split('_', 1)

        # Проверка пользователя
        if str(call.from_user.id) != user_id:
            return

        if action == "preset_1":
            apply_preset("Первый пресет", call)
        elif action == "preset_2":
            apply_preset("Второй пресет", call)
        elif action == "stop":
            stop_monitoring(call.message)
        elif action == "report":
            send_report(call.message)

    except Exception as e:
        print(f"Callback error: {e}")


def apply_preset(preset_name, call):
    """Применение пресета с уведомлением"""
    try:
        msg = bot.send_message(call.message.chat.id, f"🔄 Применяю {preset_name}...")

        # Запуск в отдельном потоке
        Thread(target=lambda: (
            run_preset(preset_name),
            bot.edit_message_text(
                f"✅ {preset_name} применен",
                chat_id=msg.chat.id,
                message_id=msg.message_id
            )
        )).start()

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")

'''commands_list = [
    control,
    report,
    stop_monitoring,
    start_monitoring,
    install_update,
    remove_update,
    hard_reset
]'''

commands_list = [
    control,
    report,
    stop_monitoring,
    #start_monitoring
]


if __name__ == '__main__':
    pass
