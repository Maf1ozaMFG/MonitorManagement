#from clicker.bin.db import get_clicker_cfg_table
from datetime import datetime, timedelta

from selenium.webdriver.support import expected_conditions as EC
import time

from selenium.webdriver.common.by import By

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException, SessionNotCreatedException
import traceback

from selenium.webdriver.support.wait import WebDriverWait

from clicker.bin.config_parse import get_item_from_config

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


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

    '''def start(self):
        try:
            # отключение ожидания загрузки окна
            caps = DesiredCapabilities().CHROME
            caps["pageLoadStrategy"] = "none"  # complete
            # =================================
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
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
            self.driver = webdriver.Chrome(glob.CDM, options=options)
            self.driver.implicitly_wait(0)
            self.driver.set_script_timeout(0.1)
            self.driver.set_page_load_timeout(0)
        except SessionNotCreatedException:
            self.start()
        except:
            print(traceback.format_exc())'''

    def start(self):
        """Оптимизированный запуск окна"""

        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = "none"

        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
            "autofill.profile_enabled": False
        }

        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.page_load_strategy = 'eager'  # Не ждём полной загрузки

        # Базовые настройки
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Отключаем ненужные функции
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")

        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("prefs", prefs)

        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            self.driver.set_page_load_timeout(15)  # Таймаут 15 секунд
        except Exception as e:
            print(f"Window {self.id} error: {e}")

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
        """Атомарное закрытие окна"""
        try:
            if not hasattr(self, 'driver') or self.driver is None:
                return True

            print(f"Закрытие окна {self.id}")
            try:
                self.driver.quit()
            except:
                pass  # Игнорируем ошибки принудительного закрытия

            self.driver = None
            return True
        except Exception as e:
            print(f"Ошибка закрытия окна {self.id}: {e}")
            return False

    #auth
    '''def auth(self):
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
            pass'''

    def auth(self):
        try:
            if not hasattr(self, 'auth_type') or not self.auth_type:
                return  # Пропускаем авторизацию для пресетов без auth_type

            current_url = self.driver.current_url
            print(f"Попытка авторизации в окне {self.id} на URL: {current_url}")

            # Для прокси авторизации (LKS)
            if 'proxy.bmstu.ru' in current_url:
                print("Обнаружена страница прокси-авторизации")
                try:
                    # Новые селекторы для прокси формы
                    username = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
                    password = self.driver.find_element(By.ID, "password")
                    submit = self.driver.find_element(By.NAME, "submit")

                    username.clear()
                    username.send_keys(get_item_from_config('AUTH')['lks_login'])

                    password.clear()
                    password.send_keys(get_item_from_config('AUTH')['lks_password'])

                    submit.click()
                    print("Данные для входа отправлены (прокси)")
                    time.sleep(3)

                except Exception as e:
                    print(f"Ошибка авторизации через прокси: {str(e)}")
                    self.driver.save_screenshot(f"proxy_auth_error_{self.id}.png")

            # Для студ почты
            if 'student.bmstu.ru' in current_url:
                print("Обнаружен студенческий портал")
                try:
                    # Явное ожидание формы авторизации
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "pronto-login")))

                    # Находим элементы по новым селекторам
                    username = self.driver.find_element(By.NAME, "username")
                    password = self.driver.find_element(By.NAME, "Password")
                    submit = self.driver.find_element(By.NAME, "login")

                    # Получаем учетные данные из конфига
                    auth_config = get_item_from_config('AUTH')

                    # Вводим данные
                    username.clear()
                    username.send_keys(auth_config['student_login'])

                    password.clear()
                    password.send_keys(auth_config['student_password'])

                    # Кликаем по кнопке
                    submit.click()
                    print("Данные для студ. портала отправлены")

                    # Проверяем успешность авторизации
                    WebDriverWait(self.driver, 5).until(
                        lambda d: "student.bmstu.ru" in d.current_url and "login" not in d.current_url)

                except Exception as e:
                    print(f"Ошибка авторизации на студ. портале: {str(e)}")

            # Скриншот результата (для отладки)
            #self.driver.save_screenshot(f"auth_result_{self.id}.png")

        except Exception as e:
            print(f"Критическая ошибка авторизации: {str(e)}")
            traceback.print_exc()



if __name__ == '__main__':
    pass
