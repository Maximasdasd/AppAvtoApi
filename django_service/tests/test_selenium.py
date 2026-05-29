"""
E2E-тесты через Selenium (опционально).

⚠️ ВАЖНО: эти тесты НЕ запускаются вместе с остальными по умолчанию.
Они требуют:
  * запущенного Django-сервиса (live_server из pytest-django ИЛИ runserver);
  * запущенного и доступного FastAPI на 127.0.0.1:8000 (иначе страницы пустые);
  * установленного Chrome/Chromium и chromedriver (webdriver-manager скачает).

Запуск только этих тестов:
    pytest tests/test_selenium.py -m selenium

Пропустить их в обычном прогоне:
    pytest -m "not selenium"

Поскольку вход в систему завязан на реальный FastAPI (логин проходит через
него), полноценный E2E-логин имеет смысл только при поднятом бэкенде с
сотрудником qweqwe/qwerty.
"""
import pytest

selenium = pytest.importorskip("selenium")  # пропустить, если selenium не стоит
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.fixture(scope="module")
def driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    drv = webdriver.Chrome(service=service, options=options)
    yield drv
    drv.quit()


@pytest.mark.selenium
class TestSeleniumE2E:
    """Базовые E2E-сценарии. Требуют live_server + запущенный FastAPI."""

    def test_login_page_has_form(self, driver, live_server):
        driver.get(f"{live_server.url}/login_staff/")
        username = driver.find_element(By.NAME, "username")
        password = driver.find_element(By.NAME, "password")
        assert username.is_displayed()
        assert password.is_displayed()

    def test_login_page_title(self, driver, live_server):
        driver.get(f"{live_server.url}/login_staff/")
        assert "AutoFleet" in driver.title

    def test_login_as_admin(self, driver, live_server):
        """
        Полноценный вход. Сработает ТОЛЬКО при запущенном FastAPI с
        сотрудником qweqwe/qwerty. Иначе вход не произойдёт.
        """
        driver.get(f"{live_server.url}/login_staff/")
        driver.find_element(By.NAME, "username").send_keys("qweqwe")
        driver.find_element(By.NAME, "password").send_keys("qwerty")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )
        assert "/dashboard" in driver.current_url
