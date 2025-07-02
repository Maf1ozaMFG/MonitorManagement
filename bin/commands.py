from bin.glob import *
from bin import glob
from bin.funcs import init_browsers, start_browsers, run_preset, allocate_browsers, send_report
from concurrent.futures import ThreadPoolExecutor
from telebot.types import BotCommand, Message
from bin.chating import start_control_chating


def start_monitoring(msg):
    """Запуск системы браузеров"""
    init_browsers()
    start_browsers()
    allocate_browsers()
    run_preset('default')


def stop_monitoring(msg):
    """Остановка всех потоков и браузеров"""
    msg = bot.send_message(msg.chat.id, 'Ожидайте закрытия всех окон')
    with ThreadPoolExecutor(max_workers=len(glob.all_windows)) as executor:
        executor.map(Window.kill, glob.all_windows)
    # bot.send_message(msg.chat.id, 'Все окна закрыты')
    bot.edit_message_text(text='Все окна закрыты', chat_id=msg.chat.id, message_id=msg.id)


def control(msg):
    """Пульт управления всеми окнами"""
    start_control_chating(msg.chat.id, msg.from_user.id, msg_id=msg.id)


def report(msg: Message):
    """Отчёт о состоянии окон"""
    send_report(msg)


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
    command_desc = [BotCommand('/' + item.__name__, item.__doc__) for item in commands_list]
    bot.set_my_commands(command_desc)


commands_list = [
    control,
    report,
    stop_monitoring,
    start_monitoring,
    install_update,
    remove_update,
    hard_reset
]


if __name__ == '__main__':
    pass
