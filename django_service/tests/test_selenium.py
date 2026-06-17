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
"""
import pytest

selenium = pytest.importorskip("selenium")  # пропустить, если selenium не стоит
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.pages.base_page import BasePage
from tests.pages.login_page import LoginPage
from tests.pages.dashboard_page import DashboardPage
from tests.pages.cars_page import CarsPage
from tests.pages.car_create_page import CarCreatePage

ADMIN_USERNAME="qweqwe"
ADMIN_PASSWORD="qwerty"


@pytest.fixture(scope="module")
def driver():
    """Один браузер на весь модуль"""
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


@pytest.fixture
def as_admin(driver, live_server):
    """
    Залогиненный браузер: проходит вход под админом и ждёт дашборд
    """
    LoginPage(driver, live_server.url).open().login(ADMIN_USERNAME, ADMIN_PASSWORD)
    DashboardPage(driver, live_server.url).wait_loaded()
    return driver


@pytest.mark.selenium
class TestLoginPage:
    """Проверки самой страницы входа (без реальной авторизации)"""

    def test_login_page_has_form(self, driver, live_server):
        # ПОЗИТИВНЫЙ: форма логина отображается
        page = LoginPage(driver, live_server.url).open()
        assert page.has_login_form()

    def test_login_page_title(self, driver, live_server):
        page = LoginPage(driver, live_server.url).open()
        assert "AutoFleet" in page.title


@pytest.mark.selenium
class TestLoginFlow:
    """Сценарии входа. Требуют запущенного FastAPI с qweqwe/qwerty"""

    def test_login_with_valid_credentials(self, driver, live_server):
        # ПОЗИТИВНЫЙ: верные данные → попадаем на дашборд
        login = LoginPage(driver, live_server.url).open()
        login.login(ADMIN_USERNAME, ADMIN_PASSWORD)

        dashboard = DashboardPage(driver, live_server.url).wait_loaded()
        assert "/dashboard" in dashboard.current_url

    def test_login_with_invalid_credentials(self, driver, live_server):
        # НЕГАТИВНЫЙ: неверный пароль → на дашборд НЕ пускает, остаёмся на логине
        login = LoginPage(driver, live_server.url).open()
        login.login(ADMIN_USERNAME, "wrong-password-123")

        # форма логина всё ещё на месте, а в URL нет /dashboard
        assert login.has_login_form()
        assert "/dashboard" not in driver.current_url