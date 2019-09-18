import time
from typing import List, Union

from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
import selenium.webdriver.support.expected_conditions as EC

from selenium.common.exceptions import NoSuchElementException
from http.client import CannotSendRequest
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import InvalidElementStateException


def sleep(func):
    def wrapper(self, *args, **kwargs):
        res = func(self, *args, **kwargs)
        time.sleep(self.config.wait)
        return res

    return wrapper


class Config(object):
    browserName: str
    browserArgs: tuple
    timeout: int = 1
    wait: int = 1
    url: str = ''
    chrome: str = 'chrome'
    firefox: str = 'firefox'
    phantomJS: str = 'phantomJS'


class Browser(object):
    browser: webdriver.Chrome
    wait: WebDriverWait
    actions: ActionChains
    config: Config
    selector: str = By.CSS_SELECTOR

    def __init__(self, timeout=10):
        self.config = Config()
        self.config.timeout = timeout

    def initChrome(self, driver: str):
        self.config.browserName = self.config.chrome
        self.config.browserArgs = (driver,)
        self.browser = webdriver.Chrome(driver)
        self.initAfterBrowser()

    def initFirefox(self, driver: str, binary: str):
        self.config.browserName = self.config.firefox
        self.config.browserArgs = (driver, binary)
        self.browser = webdriver.Firefox(firefox_binary=FirefoxBinary(binary), executable_path=driver)
        self.initAfterBrowser()

    def initPhantomJS(self, driver: str):
        self.config.browserName = self.config.phantomJS
        self.config.browserArgs = (driver,)
        self.browser = webdriver.PhantomJS(executable_path=driver)
        self.initAfterBrowser()

    @sleep
    def initAfterBrowser(self):
        self.wait = WebDriverWait(self.browser, self.config.timeout)
        self.actions = ActionChains(self.browser)

    def newSession(self):
        assert self.config.browserName
        if self.config.browserName == self.config.chrome:
            self.initChrome(*self.config.browserArgs)
        elif self.config.browserName == self.config.firefox:
            self.initFirefox(*self.config.browserArgs)
        elif self.config.browserName == self.config.phantomJS:
            self.initPhantomJS(*self.config.browserArgs)
        else:
            raise StopIteration(self.config.browserName)

    def findElement(self, path: str) -> WebElement:
        return self.browser.find_element(self.selector, path)

    def findElements(self, path: str) -> List[WebElement]:
        return self.browser.find_elements(self.selector, path)

    def findElementFrom(self, element: WebElement, path: str) -> WebElement:
        return element.find_element(self.selector, path)

    def findElementsFrom(self, element: WebElement, path: str) -> List[WebElement]:
        return element.find_elements(self.selector, path)

    def getText(self, element: Union[WebElement, List[WebElement]]) -> Union[str, list]:
        if type(element) is list:
            return [i.text.strip() for i in element]
        else:
            return element.text.strip()

    def getAttribute(self, element: Union[WebElement, List[WebElement]], name: str) -> Union[str, list]:
        if type(element) is list:
            return [i.get_attribute(name).strip() for i in element]
        else:
            return element.get_attribute(name).strip()

    @sleep
    def clearForm(self, element: WebElement):
        element.clear()

    @sleep
    def fillForm(self, element: WebElement, value: str):
        element.send_keys(value)

    @sleep
    def click(self, element: WebElement, wait=None, timeout=None):
        element.click()

    @sleep
    def moveCursor(self, element: WebElement):
        self.actions.reset_actions()
        self.actions.move_to_element(element)
        self.actions.perform()

    @sleep
    def refresh(self):
        self.browser.refresh()

    def getCookies(self):
        return self.browser.get_cookies()

    def setCookies(self, cookies):
        for cookie in cookies:
            self.browser.add_cookie(cookie)

    def isDisplayed(self, element: WebElement, wait=None):
        return element.is_displayed()

    @sleep
    def go(self, url, refresh=False, timeout=None):
        self.config.url = url
        self.browser.get(url)

    def addToDoOnNewSession(self, func, *args, **kwargs):
        pass

    def waitAvailable(self, waitAvailablePath, emptyPath=None, printer=True, timeout=None):
        pass
