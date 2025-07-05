from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def test_chrome():
    try:
        service = Service(ChromeDriverManager().install())

        options = Options()
        options.add_argument("--start-maximized")

        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://google.com")
        print("✅ Chrome успешно запущен!")
        input("Нажмите Enter для закрытия...")
        driver.quit()
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    test_chrome()