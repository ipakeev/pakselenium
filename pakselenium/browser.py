import sys
import traceback
import time
from typing import List, Tuple, Callable, Union, Optional

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


def isReachedCondition(until: Union[Callable, Tuple[Callable]]):
    if until is None:
        return True

    if type(until) is tuple:
        for i in until:
            if not i():
                return False
        return True
    else:
        if until():
            return True


def isEmpty(empty: Callable):
    if empty is None:
        return False
    return empty()


def isReload(reload: Callable):
    if reload is None:
        return False
    return reload()


def EC_isVisible(element):
    def wrapper(_):
        return element.is_displayed()

    return wrapper


def catchStaleElementReferenceException(func):
    def wrapper(self, *args, **kwargs):
        while 1:
            try:
                return func(self, *args, **kwargs)
            except StaleElementReferenceException:
                # when element is updating
                # exc_info = sys.exc_info()
                # traceback.print_exception(*exc_info)
                pass
            except Exception as e:
                print(func, args, kwargs)
                raise e
            time.sleep(1)

    return wrapper


class PageElement(object):
    element: WebElement
    text: str

    def __init__(self, element: WebElement):
        self.element = element
        self.text = self.element.text.strip()

    def isDisplayed(self):
        return self.element.is_displayed()

    def getAttribute(self, name):
        return self.element.get_attribute(name)


class Config(object):
    browserName: str
    browserArgs: tuple
    timeoutWait: int = 10
    sleep: int = 1
    implicitWait: int = 0
    url: str = ''
    chrome: str = 'chrome'
    firefox: str = 'firefox'
    phantomJS: str = 'phantomJS'
    element: PageElement


class Browser(object):
    browser: webdriver.Chrome
    wait: WebDriverWait
    actions: ActionChains
    config: Config
    selector: str = By.CSS_SELECTOR

    def __init__(self):
        self.config = Config()

    def initChrome(self, driver: str):
        self.config.browserName = self.config.chrome
        self.config.browserArgs = (driver,)
        self.browser = webdriver.Chrome(executable_path=driver)
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

    def initAfterBrowser(self):
        self.browser.implicitly_wait(self.config.implicitWait)
        self.wait = WebDriverWait(self.browser, self.config.timeoutWait)
        self.actions = ActionChains(self.browser)
        self.sleep()

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

    def sleep(self, sec: Optional[int] = None):
        sec = sec or self.config.sleep
        time.sleep(sec or self.config.sleep)

    def isOnPage(self, path: str) -> bool:
        try:
            self.browser.find_element(self.selector, path)
            return True
        except NoSuchElementException:
            return False

    @catchStaleElementReferenceException
    def findElement(self, path: str) -> PageElement:
        self.config.element = path
        assert self.isOnPage(path)
        element = self.browser.find_element(self.selector, path)
        return PageElement(element)

    @catchStaleElementReferenceException
    def findElements(self, path: str) -> List[PageElement]:
        self.config.element = path
        assert self.isOnPage(path)
        es = self.browser.find_elements(self.selector, path)
        pes = []
        for element in es:
            pes.append(PageElement(element))
        return pes

    @catchStaleElementReferenceException
    def findElementFrom(self, pe: PageElement, path: str) -> PageElement:
        self.config.element = pe, path
        element = pe.element.find_element(self.selector, path)
        return PageElement(element)

    @catchStaleElementReferenceException
    def findElementsFrom(self, pe: PageElement, path: str) -> List[PageElement]:
        self.config.element = pe, path
        es = pe.element.find_elements(self.selector, path)
        pes = []
        for element in es:
            pes.append(PageElement(element))
        return pes

    def clearForm(self, pe: PageElement):
        self.config.element = pe
        self.wait.until(EC_isVisible(pe.element))
        pe.element.clear()
        self.sleep()

    def fillForm(self, pe: PageElement, value: str):
        self.config.element = pe
        self.wait.until(EC_isVisible(pe.element))
        pe.element.send_keys(value)
        self.sleep()

    def moveCursor(self, pe: PageElement):
        self.config.element = pe
        self.wait.until(EC_isVisible(pe.element))
        self.actions.reset_actions()
        self.actions.move_to_element(pe.element)
        self.actions.perform()
        self.sleep()

    def click(self, pe: PageElement, until: Union[Callable, Tuple[Callable, ...]] = None,
              empty: Callable = None, reload: Callable = None):
        self.config.element = pe
        self.wait.until(EC_isVisible(pe.element))
        pe.element.click()
        self.sleep()
        tt = time.time()
        while 1:
            if isEmpty(empty):
                return
            if isReload(reload):
                self.browser.refresh()
                self.sleep(5)
                continue
            if isReachedCondition(until):
                return
            if time.time() - tt >= 20:
                print('>!> delay clicking "{}" button'.format(pe.text))
                self.browser.refresh()
                self.sleep(5)
                tt = time.time()
                continue
            self.sleep(2)

    def go(self, url, until: Union[Callable, Tuple[Callable, ...]] = None,
           empty: Callable = None, reload: Callable = None):
        self.config.url = url
        while 1:
            self.browser.get(url)
            try:
                self.config.element = url
                self.wait.until(EC.url_to_be(url))
            except TimeoutException:
                time.sleep(5)
                continue
            if isEmpty(empty):
                return
            if isReload(reload):
                self.browser.refresh()
                self.sleep(5)
                continue
            if isReachedCondition(until):
                break

    def refresh(self, until: Union[Callable, Tuple[Callable, ...]] = None):
        while 1:
            self.browser.refresh()
            time.sleep(5)
            if isReachedCondition(until):
                break

    @property
    def currentUrl(self):
        return self.browser.current_url

    def getCookies(self):
        return self.browser.get_cookies()

    def setCookies(self, cookies):
        for cookie in cookies:
            if 'expiry' in cookie:
                del cookie['expiry']
            self.browser.add_cookie(cookie)
