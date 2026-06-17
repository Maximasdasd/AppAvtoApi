from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    """Базовый класс. Общие действия для всех страниц (наследуются ниже)."""

    PATH = ""  # переопределяется в наследниках

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url.rstrip("/")

    def open(self, path=None):
        """Открыть страницу. По умолчанию — PATH самого Page Object."""
        target = self.PATH if path is None else path
        self.driver.get(f"{self.base_url}{target}")
        return self

    # — низкоуровневые помощники —
    def find(self, locator):
        """locator — это кортеж вида (By.NAME, 'username')."""
        return self.driver.find_element(*locator)

    def find_all(self, locator):
        return self.driver.find_elements(*locator)

    def type(self, locator, text):
        el = self.find(locator)
        el.clear()
        el.send_keys(text)
        return self

    def click(self, locator):
        self.find(locator).click()
        return self

    # — ожидания (Selenium не ждёт сам, поэтому ждём явно) —
    def wait_visible(self, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )

    def wait_url_contains(self, fragment, timeout=10):
        WebDriverWait(self.driver, timeout).until(EC.url_contains(fragment))
        return self

    # — свойства-обёртки, чтобы тесты не лезли в self.driver напрямую —
    @property
    def title(self):
        return self.driver.title

    @property
    def current_url(self):
        return self.driver.current_url

    def is_visible(self, locator, timeout=5):
        """True, если элемент появился за timeout сек, иначе False."""
        try:
            self.wait_visible(locator, timeout)
            return True
        except Exception:
            return False
