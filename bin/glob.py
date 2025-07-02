import os
from telebot import apihelper, TeleBot
import sys
from bin.db import *
from bin.logger import create_logger
from bin.objects import Window
from webdriver_manager.chrome import ChromeDriverManager


logger = create_logger('sam')
auth_info = get_item_from_config("AUTH")
all_windows = [Window]
CDM = os.path.join(os.getcwd(), 'chromedriver.exe')
token = get_item_from_config('BOT')['test_token']
# bot.users_vars = [dict()]

if os.environ['COMPUTERNAME'] == '2112FS000340':
    apihelper.proxy = {
      'http': 'http://dmz-is-wdz-01.csnp.cea.gov.ru:3128',
      'https': 'http://dmz-is-wdz-01.csnp.cea.gov.ru:3128'
    }
    token = get_item_from_config('BOT')['token']
# else:
#     CDM = os.path.join(os.getcwd(), 'chromedriver_local.exe')
    # CDM = ChromeDriverManager().install()

bot = TeleBot(token, parse_mode='HTML')
if len(sys.argv) > 2:
    bot.send_message(sys.argv[1], f'{sys.argv[2]} completed')


if __name__ == '__main__':
    pass

