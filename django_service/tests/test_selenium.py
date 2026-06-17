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
    Залогиненный браузер: проходит вход под админом и ждёт дашборд.
    """
    LoginPage(driver, live_server.url).open().login(ADMIN_USERNAME, ADMIN_PASSWORD)

    # --- ВРЕМЕННАЯ ДИАГНОСТИКА (потом удалить) ---
    import time
    time.sleep(2)  # даём форме отправиться
    print("\n\n===== ПОСЛЕ ЛОГИНА =====")
    print("URL:", driver.current_url)
    print("TITLE:", driver.title)
    print("HTML (первые 2000 символов):")
    print(driver.page_source[:2000])
    print("===== КОНЕЦ =====\n\n")
    # --- конец диагностики ---

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


@pytest.mark.selenium
class TestDashboard:
    """Дашборд после входа (используем фикстуру as_admin)"""

    def test_dashboard_title(self, as_admin, live_server):
        page = DashboardPage(as_admin, live_server.url).open()
        assert "Дашборд" in page.title

    def test_dashboard_shows_stat_cards(self, as_admin, live_server):
        # ПОЗИТИВНЫЙ: на дашборде есть карточки статистики
        page = DashboardPage(as_admin, live_server.url).open()
        assert len(page.stat_cards()) > 0


@pytest.mark.selenium
class TestCars:
    """Переход к машинам и работа со списком (нужна авторизация)"""

    def test_navigate_from_dashboard_to_cars(self, as_admin, live_server):
        # ПОЗИТИВНЫЙ: клик по «Автомобили» в меню ведёт на /cars
        dashboard = DashboardPage(as_admin, live_server.url).open()
        cars = dashboard.go_to_cars()
        cars.wait_url_contains("/cars")
        assert "/cars" in cars.current_url

    def test_cars_page_title(self, as_admin, live_server):
        page = CarsPage(as_admin, live_server.url).open()
        assert "Автомобили" in page.title

    def test_cars_page_has_add_button(self, as_admin, live_server):
        # ПОЗИТИВНЫЙ: кнопка «+ Добавить авто» присутствует
        page = CarsPage(as_admin, live_server.url).open()
        assert page.has_add_button()

    def test_cars_search_returns_results(self, as_admin, live_server):
        # Ищем по заведомо широкому запросу; страница не падает, поиск отрабатывает.
        # (Конкретное число строк зависит от данных в FastAPI.)
        page = CarsPage(as_admin, live_server.url).open()
        page.search("A")
        page.wait_url_contains("search=")
        assert "search=" in page.current_url



@pytest.mark.selenium
class TestCreateCarFlow:
    """
    вход  список авто  форма  создание возврат на список
    ПОЗИТИВНЫй
    """

    def test_create_car_redirects_to_list(self, as_admin, live_server):
        cars = CarsPage(as_admin, live_server.url).open()
        form = cars.open_create_form()
        form.wait_url_contains("/cars/create")

        form.create(
            brand="TestBrand",
            year=2022,
            number="T999TT",
            price=3500,
            category="STANDARD",
            color="white",
        )

        # после успешного создания view делает redirect('cars') → /cars/
        cars.wait_url_contains("/cars")
        assert "/cars" in cars.current_url
        assert "/cars/create" not in cars.current_url
