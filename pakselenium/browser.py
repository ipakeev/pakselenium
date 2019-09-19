import sys
import traceback
import time
from typing import List, Tuple, Dict, Callable, Union, Optional

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


def catchExceptions(func):
    def wrapper(self, *args, **kwargs):
        while 1:
            try:
                res = func(self, *args, **kwargs)
                break
            except StaleElementReferenceException:
                # when element is updating
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
            except:
                print(func, args, kwargs)
                raise
            time.sleep(1)
        return res

    return wrapper


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


def cycle_text(element: WebElement):
    while 1:
        try:
            return element.text.strip()
        except StaleElementReferenceException:
            # when element is updating
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            time.sleep(1)


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
    element: WebElement


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

    def findElement(self, path: str) -> WebElement:
        self.config.element = path
        assert self.isOnPage(path)
        element = self.browser.find_element(self.selector, path)
        self.config.element = element
        assert element is not None
        return element

    def findElements(self, path: str) -> List[WebElement]:
        self.config.element = path
        assert self.isOnPage(path)
        elements = self.browser.find_elements(self.selector, path)
        self.config.element = elements
        assert elements is not None
        return elements

    def findElementFrom(self, element: WebElement, path: str) -> WebElement:
        self.config.element = element, path
        return element.find_element(self.selector, path)

    def findElementsFrom(self, element: WebElement, path: str) -> List[WebElement]:
        self.config.element = element, path
        return element.find_elements(self.selector, path)

    def getText(self, element: Union[WebElement, List[WebElement]]) -> Union[str, list]:
        if type(element) is list:
            texts = []
            for i in element:
                self.config.element = i
                texts.append(cycle_text(i))
            return texts
        else:
            self.config.element = element
            return cycle_text(element)

    def getAttribute(self, element: Union[WebElement, List[WebElement]], name: str) -> Union[str, list]:
        if type(element) is list:
            texts = []
            for i in element:
                self.config.element = i
                texts.append(i.get_attribute(name).strip())
            return texts
        else:
            self.config.element = element
            return element.get_attribute(name).strip()

    def getDictOfElements(self, elements: List[WebElement]) -> Dict[str, WebElement]:
        names = self.getText(elements)
        return {name: elem for name, elem in zip(names, elements)}

    def clearForm(self, element: WebElement):
        self.config.element = element
        self.wait.until(EC_isVisible(element))
        element.clear()
        self.sleep()

    def fillForm(self, element: WebElement, value: str):
        self.config.element = element
        self.wait.until(EC_isVisible(element))
        element.send_keys(value)
        self.sleep()

    def moveCursor(self, element: WebElement):
        self.config.element = element
        self.wait.until(EC_isVisible(element))
        self.actions.reset_actions()
        self.actions.move_to_element(element)
        self.actions.perform()
        self.sleep()

    def click(self, element: WebElement, until: Union[Callable, Tuple[Callable, ...]] = None,
              empty: Callable = None, reload: Callable = None):
        text = self.getText(element)
        self.config.element = element
        self.wait.until(EC_isVisible(element))
        element.click()
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
                print('>!> delay clicking "{}" button'.format(text))
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

    @staticmethod
    def isDisplayed(element: WebElement):
        return element.is_displayed()

    def addToDoOnNewSession(self, func, *args, **kwargs):
        pass

    def waitAvailable(self, waitAvailablePath, emptyPath=None, printer=True, timeout=None):
        pass
