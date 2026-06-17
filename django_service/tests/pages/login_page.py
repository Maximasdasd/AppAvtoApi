from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.pages.base_page import BasePage   # потому что LoginPage(BasePage)

class LoginPage(BasePage):
    """Страница входа. Рендерится на корне '/'."""

    PATH = "/"

    USERNAME = (By.NAME, "username")
    PASSWORD = (By.NAME, "password")
    SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")

    def login(self, username, password):
        """Заполнить форму и нажать «Войти»."""
        self.type(self.USERNAME, username)
        self.type(self.PASSWORD, password)
        self.click(self.SUBMIT)
        return self

    def has_login_form(self):
        """Видна ли форма логина (оба поля)."""
        return self.is_visible(self.USERNAME) and self.is_visible(self.PASSWORD)