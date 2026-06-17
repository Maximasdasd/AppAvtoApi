from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.pages.base_page import BasePage   # потому что LoginPage(BasePage)

class CarsPage(BasePage):
    """Список автомобилей."""

    PATH = "/cars/"

    SEARCH_INPUT = (By.NAME, "search")
    # кнопка «Найти» внутри GET-формы поиска
    SEARCH_SUBMIT = (By.CSS_SELECTOR, "form[method='get'] button[type='submit']")
    ADD_CAR_BTN = (By.LINK_TEXT, "+ Добавить авто")
    STATUS_TABS = (By.CSS_SELECTOR, ".tab")
    TABLE_ROWS = (By.CSS_SELECTOR, "table tbody tr")

    def search(self, query):
        """Ввести запрос в поиск и нажать «Найти»."""
        self.type(self.SEARCH_INPUT, query)
        self.click(self.SEARCH_SUBMIT)
        return self

    def rows(self):
        """Список строк таблицы машин."""
        return self.find_all(self.TABLE_ROWS)

    def rows_count(self):
        return len(self.rows())

    def has_add_button(self):
        return self.is_visible(self.ADD_CAR_BTN)

    def open_create_form(self):
        """Нажать «+ Добавить авто» и вернуть CarCreatePage."""
        self.click(self.ADD_CAR_BTN)
        return CarCreatePage(self.driver, self.base_url)
