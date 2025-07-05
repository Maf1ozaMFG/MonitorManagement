from datetime import datetime
import os
from py7zr import SevenZipFile
import shutil
import sys
import traceback
from time import sleep
from telebot import TeleBot, apihelper


def edit_msg(sender, add_text):
    for i in range(10):
        try:
            sender.edit_message_text(
                chat_id=sender.main_msg.chat.id,
                message_id=sender.main_msg.id,
                text=sender.main_msg.text + add_text
            )
        except:
            sleep(5)


def get_params():
    try:
        _, param1, param2, param3, param4 = sys.argv
        return param1, param2, param3, param4
    except:
        print('ERROR: invalid set of parameters')
        sleep(30)
        exit()


def stop_clicker(name):
    process_killed = False
    for _ in range(10):
        print(f'Try kill {name}.exe')
        os.system(f"taskkill /F /T /IM {name}.exe")
        os.system(f"taskkill /F /T /IM chrome.exe")
        bot_exist = os.popen(f'''wmic process get description, processid | findstr "{name}"''').read()
        chrome_exist = os.popen(f'''wmic process get description, processid | findstr "chrome"''').read()
        if not bot_exist and not chrome_exist:
            process_killed = True
            break
    return process_killed


def main_restart(sender, proc_name):
    if stop_clicker(proc_name):
        edit_msg(sender, f'\n{proc_name}.exe stopped')
    else:
        edit_msg(sender, f'\nUnable to kill the process {proc_name}.exe')
        exit()
    print(f'start {proc_name}')
    os.popen(f"start {proc_name}.exe {bot.main_msg.chat.id} restart")
    edit_msg(sender, f'\n{proc_name}.exe started')


def unpack_files(sender, proc_name):
    edit_msg(sender, f"\nUnpack {proc_name}")
    try:
        files = sorted(os.listdir('received'))
        files = list(filter(lambda x: proc_name in x, files))
        if not files:
            edit_msg(sender, f'\nUPDATE FAILED. No files for update {proc_name}')
            exit()
        with open(f'{proc_name}.7z', 'ab') as outfile:
            for file in files:
                with open(os.path.join('received', file), 'rb') as infile:
                    outfile.write(infile.read())
        with SevenZipFile(f'{proc_name}.7z', 'r') as archive:
            archive.extractall('unpacked')
        unpacked = os.listdir('unpacked')
        if unpacked[0] != f'{proc_name}.exe':
            edit_msg(sender, f'\nUPDATE FAILED. Wrong received file')
            exit()
        return True
    except:
        text = f"\nUPDATE FAILED.\n" \
               f"Information in the console, there is 1 minute left before closing.\n" \
               f"The clock's ticking"
        edit_msg(sender, text)
        print(traceback.format_exc())
        sleep(60)
        exit()


def main_updater(sender, proc_name):
    # check system folders
    for folder in ['unpacked', 'backup']:
        os.makedirs(folder) if not os.path.exists(folder) else None
    print('Unpacking files')
    unpack_files(sender, proc_name)

    print(f'Stop {proc_name}')
    stop_clicker(proc_name)

    print('Create backup')
    new_name = datetime.now().strftime(f'{proc_name}.exe_%d.%m.%Y.%H.%M')
    shutil.move(f"{proc_name}.exe", os.path.join('backup', new_name))

    print(f'Replace new {proc_name}.exe')
    shutil.move(os.path.join('unpacked', f"{proc_name}.exe"), f"{proc_name}.exe")

    os.popen(f"start {proc_name}.exe {sender.main_msg.chat.id} update")
    edit_msg(sender, f'\n{proc_name}.exe started')

    print(f'Delete temp files')
    for folder in ['unpacked', 'received']:
        shutil.rmtree(folder)
    os.remove(f'{proc_name}.7z')


if __name__ == '__main__':
    action, process_name, chat_id, token = get_params()
    if os.environ['COMPUTERNAME'] == '2112FS000340':
        apihelper.proxy = {
          'http': 'http://dmz-is-wdz-01.csnp.cea.gov.ru:3128',
          'https': 'http://dmz-is-wdz-01.csnp.cea.gov.ru:3128'
        }
    bot = TeleBot(token)
    bot.main_msg = bot.send_message(chat_id, f'Action: {action} {process_name}')
    if action == 'restart':
        main_restart(bot, process_name)
    if action == 'update':
        main_updater(bot, process_name)
