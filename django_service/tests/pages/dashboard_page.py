from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.pages.base_page import BasePage   # потому что LoginPage(BasePage)

class DashboardPage(BasePage):
    """Дашборд. Доступен после успешного входа."""

    PATH = "/dashboard"

    STAT_CARDS = (By.CSS_SELECTOR, ".stat-card")
    STAT_VALUES = (By.CSS_SELECTOR, ".stat-value")
    LOGOUT_LINK = (By.LINK_TEXT, "Выйти")

    # ссылки бокового меню (sidebar из base.html)
    NAV_CARS = (By.CSS_SELECTOR, "a.nav-link[href='/cars']")
    NAV_CLIENTS = (By.CSS_SELECTOR, "a.nav-link[href='/clients']")
    NAV_RENTALS = (By.CSS_SELECTOR, "a.nav-link[href='/rentals']")
    NAV_REPAIRS = (By.CSS_SELECTOR, "a.nav-link[href='/repairs']")

    def wait_loaded(self):
        """Дождаться, пока URL действительно станет дашбордом."""
        return self.wait_url_contains("/dashboard")

    def stat_cards(self):
        return self.find_all(self.STAT_CARDS)

    def go_to_cars(self):
        """Кликнуть по «Автомобили» в меню и вернуть CarsPage."""
        self.click(self.NAV_CARS)
        return CarsPage(self.driver, self.base_url)