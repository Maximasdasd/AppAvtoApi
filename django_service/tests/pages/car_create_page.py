from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.pages.base_page import BasePage   # потому что LoginPage(BasePage)

class CarCreatePage(BasePage):
    """Форма создания автомобиля."""

    PATH = "/cars/create/"

    BRAND = (By.NAME, "brand")
    YEAR = (By.NAME, "year_release")
    NUMBER = (By.NAME, "number_car")
    PRICE = (By.NAME, "daily_price")
    CATEGORY = (By.NAME, "category")  # ECONOMY / STANDARD / PREMIUM / LUX
    COLOR = (By.NAME, "color")
    SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")

    def fill(self, brand, year, number, price, category, color):
        self.type(self.BRAND, brand)
        self.type(self.YEAR, str(year))
        self.type(self.NUMBER, number)
        self.type(self.PRICE, str(price))
        self.type(self.CATEGORY, category)
        self.type(self.COLOR, color)
        return self

    def submit(self):
        self.click(self.SUBMIT)
        return self

    def create(self, brand, year, number, price, category, color):
        """Заполнить всё и отправить за один вызов."""
        return self.fill(brand, year, number, price, category, color).submit()