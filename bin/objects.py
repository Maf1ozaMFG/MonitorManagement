from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException, SessionNotCreatedException
import traceback

from bin.config_parse import get_item_from_config
from bin.db import get_clicker_cfg_table
from bin import glob


class Window:
    # identifiers
    id = 0
    mon_num, win_num = 0, 0

    # window parameters
    driver = None
    x, y, width, height = 0, 0, 0, 0
    position = None
    blocked_by = None

    # mon params
    mon_x, mon_y, mon_width, mon_height = 0, 0, 0, 0

    # offsets
    zero_x, zero_y = 0, 0

    # task parameters
    task_name = None
    filter = None
    cur_task = None
    button_number = 0
    timeout = 30
    button_timestamp = datetime.now() - timedelta(hours=1)
    refresh_timestamp = datetime.now() - timedelta(hours=1)

    new_task = True
    pause = False
    online = True

    def __init__(self, monitor_num, window_num, monitor_cfg):
        # идентификаторы окна
        self.mon_num = monitor_num
        self.win_num = window_num
        self.id = int(f'{monitor_num}{window_num}')
        # координаты и размеры текущего экрана
        self.mon_x = monitor_cfg.x
        self.mon_y = monitor_cfg.y
        self.mon_width = monitor_cfg.width
        self.mon_height = monitor_cfg.height
        # определение размеров и положения окна с учётом погрешности
        offsets = get_item_from_config('OFFSETS')
        self.zero_x = self.mon_x + int(offsets["x_error"])
        self.zero_y = self.mon_y + int(offsets["y_error"])
        x_y_coords = {
            1: dict(x=self.zero_x, y=self.zero_y),
            2: dict(x=self.zero_x + self.mon_width // 2, y=self.zero_y),
            3: dict(x=self.zero_x + self.mon_width // 2, y=self.zero_y + self.mon_height // 2),
            4: dict(x=self.zero_x, y=self.zero_y + self.mon_height // 2)
        }
        self.x, self.y = x_y_coords.get(self.win_num).values()
        self.width = (self.mon_width + int(offsets["width_error"])) // 2
        self.height = (self.mon_height + int(offsets["height_error"])) // 2

    def start(self):
        try:
            # отключение ожидания загрузки окна
            caps = DesiredCapabilities().CHROME
            caps["pageLoadStrategy"] = "none"  # complete
            # =================================
            options = webdriver.ChromeOptions()
            html_content = f"""
                data:text/html;charset=utf-8,
                <html>
                     <head><title>Hello World =)</title></head>
                     <body><div>Hello World =)
                     </div></body>
                </html>
            """
            args = ["--incognito",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-infobars",
                    "--disable-extensions",
                    "--disable-gpu",
                    f"--window-position=0,-5000",
                    f"--app={html_content}"]
            for argument in args:
                options.add_argument(argument)
            # отключение всплывающего окна об автоматизированном ПО
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            self.driver = webdriver.Chrome(glob.CDM,
                                           desired_capabilities=caps,
                                           options=options)
            self.driver.implicitly_wait(0)
            self.driver.set_script_timeout(0.1)
            self.driver.set_page_load_timeout(0)
        except SessionNotCreatedException:
            self.start()
        except:
            print(traceback.format_exc())

    def set_fullscreen(self):
        try:
            self.driver.set_window_position(self.zero_x, self.zero_y)
            self.driver.maximize_window()
            self.driver.switch_to.window(self.driver.current_window_handle)
        except:
            print('set_fullscreen')
            print(traceback.format_exc())

    def set_minimize(self):
        try:
            self.driver.minimize_window()
            self.online = False
        except InvalidSessionIdException:
            pass
        except:
            print('set_minimize')
            print(traceback.format_exc())

    def up_side(self):
        allowed = [1, 2]
        if self.win_num in allowed:
            allowed.remove(self.win_num)
            self.driver.set_window_position(self.zero_x, self.zero_y)
            self.driver.set_window_size(self.width*2, self.height)

    def down_side(self):
        avail = [4, 3]
        if self.win_num in avail:
            avail.remove(self.win_num)
            self.driver.set_window_position(self.zero_x, self.zero_y + self.mon_height // 2)
            self.driver.set_window_size(self.width*2, self.height)

    def left_side(self):
        avail = [4, 1]
        if self.win_num in avail:
            avail.remove(self.win_num)
            self.driver.set_window_position(self.zero_x, self.zero_y)
            self.driver.set_window_size(self.width, self.height*2)

    def right_side(self):
        avail = [3, 2]
        if self.win_num in avail:
            avail.remove(self.win_num)
            self.driver.set_window_position(self.zero_x + self.mon_width // 2, self.zero_y)
            self.driver.set_window_size(self.width, self.height*2)

    def set_title(self, reason=None):
        time_left = ''
        if self.refresh_timestamp:
            seconds_left = self.timeout - (datetime.now() - self.refresh_timestamp).seconds
            time_left = "Уже скоро" if seconds_left < 0 else f"{seconds_left}s ({self.timeout})"
        if reason:
            time_left = reason
        text_arr = [self.id, self.task_name, self.filter, time_left]
        title = f'''
            document.title = "{' '.join([str(item) for item in text_arr if item])}"
                    '''
        try:
            self.driver.execute_script(title)
        except TimeoutException:
            pass

    def def_allocation(self):
        try:
            self.driver.set_window_position(self.x, self.y)
            self.driver.set_window_size(self.width, self.height)
            self.blocked_by = None
            self.position = 'standard'
        except:
            print('rest_def_allocation')
            print(traceback.format_exc())
            self.start()

    def kill(self):
        try:
            self.task_name = None
            self.driver.close()
            self.driver.quit()
        except:
            pass

    def auth(self):
        try:
            filter_rule = [name for name, url in glob.auth_info.items() if url in self.driver.current_url]
            if filter_rule:
                cfg = get_item_from_config(filter_rule[0].upper())
                # driver.find_element_by_xpath(
                #     "//div[@aria-label='Any time']/div[@class='mn-hd-txt' and text()='Any time']");
                login_field = self.driver.find_element(by=cfg['login_by'], value=cfg['login_field'])
                pass_field = self.driver.find_element(by=cfg['pass_by'], value=cfg['pass_field'])
                login_btn = self.driver.find_element(by=cfg['login_btn_by'], value=cfg['login_btn'])
                if login_field and pass_field and login_btn:
                    print(f'{self.id} try auth {filter_rule[0].upper()}')
                    login_field.clear()
                    pass_field.clear()
                    login_field.send_keys(cfg['user'])
                    pass_field.send_keys(cfg['pass'])
                    login_btn.click()
        except Exception:
            pass


if __name__ == '__main__':
    pass
