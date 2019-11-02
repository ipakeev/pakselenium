import time
from typing import List, Tuple, Callable, Union

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement

from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
# from urllib3.exceptions import MaxRetryError

from .utils import callable_conditions as CC
from .utils import expected_conditions as EC
from .utils import catch


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
    browserKwargs: dict
    timeoutWait: int = 10
    implicitWait: int = 0
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

    def __init__(self):
        self.config = Config()

    def initChrome(self, driver: str, headless=False, args=None):
        options = Options()
        options.headless = headless
        if args:
            for arg in args:
                options.add_argument(arg)

        self.config.browserName = self.config.chrome
        self.config.browserKwargs = {
            'driver': driver,
            'headless': headless,
            'args': args,
        }
        self.browser = webdriver.Chrome(executable_path=driver, options=options)
        self.initAfterBrowser()

    def initFirefox(self, driver: str, binary: str):
        self.config.browserName = self.config.firefox
        self.config.browserKwargs = {
            'driver': driver,
            'binary': binary,
        }
        self.browser = webdriver.Firefox(executable_path=driver, firefox_binary=FirefoxBinary(binary))
        self.initAfterBrowser()

    def initPhantomJS(self, driver: str):
        self.config.browserName = self.config.phantomJS
        self.config.browserKwargs = {
            'driver': driver,
        }
        self.browser = webdriver.PhantomJS(executable_path=driver)
        self.initAfterBrowser()

    def initAfterBrowser(self):
        self.browser.implicitly_wait(self.config.implicitWait)
        self.wait = WebDriverWait(self.browser, self.config.timeoutWait)
        self.actions = ActionChains(self.browser)
        time.sleep(1.0)

    def newSession(self):
        assert self.config.browserName
        self.close()
        if self.config.browserName == self.config.chrome:
            self.initChrome(**self.config.browserKwargs)
        elif self.config.browserName == self.config.firefox:
            self.initFirefox(**self.config.browserKwargs)
        elif self.config.browserName == self.config.phantomJS:
            self.initPhantomJS(**self.config.browserKwargs)
        else:
            raise StopIteration(self.config.browserName)

    def close(self):
        try:
            self.browser.close()
        except WebDriverException:
            pass

    def isOnPage(self, path: str) -> bool:
        try:
            self.browser.find_element(self.selector, path)
            return True
        except NoSuchElementException:
            return False

    @catch.staleElementReferenceException
    def findElement(self, path: str) -> PageElement:
        assert self.isOnPage(path)
        element = self.browser.find_element(self.selector, path)
        return PageElement(element)

    @catch.staleElementReferenceException
    def findElements(self, path: str) -> List[PageElement]:
        assert self.isOnPage(path)
        es = self.browser.find_elements(self.selector, path)
        pes = []
        for element in es:
            pes.append(PageElement(element))
        return pes

    @catch.staleElementReferenceException
    def findElementFrom(self, pe: PageElement, path: str) -> PageElement:
        element = pe.element.find_element(self.selector, path)
        return PageElement(element)

    @catch.staleElementReferenceException
    def findElementsFrom(self, pe: PageElement, path: str) -> List[PageElement]:
        es = pe.element.find_elements(self.selector, path)
        pes = []
        for element in es:
            pes.append(PageElement(element))
        return pes

    def clearForm(self, pe: PageElement):
        self.wait.until(EC.isVisible(pe.element))
        pe.element.clear()
        time.sleep(0.5)

    def fillForm(self, pe: PageElement, value: str):
        self.wait.until(EC.isVisible(pe.element))
        pe.element.send_keys(value)
        time.sleep(0.5)

    def moveCursor(self, pe: PageElement):
        self.wait.until(EC.isVisible(pe.element))
        self.actions.reset_actions()
        self.actions.move_to_element(pe.element)
        self.actions.perform()
        time.sleep(1.0)

    def isReachedPage(self,
                      until: Union[Callable, Tuple[Callable, ...]],
                      untilOr: Tuple[Callable, ...],
                      empty: Callable,
                      reload: Callable) -> bool:
        tt = time.time()
        while 1:
            if CC.isEmpty(empty):
                return True
            if CC.isReload(reload):
                self.browser.refresh()
                continue
            if CC.isReached(until, untilOr):
                return True
            if time.time() - tt >= self.config.timeoutWait:
                return False
            time.sleep(0.5)

    def click(self,
              pe: PageElement,
              until: Union[Callable, Tuple[Callable, ...]] = None,
              untilOr: Tuple[Callable, ...] = None,
              empty: Callable = None,
              reload: Callable = None):
        self.wait.until(EC.isVisible(pe.element))
        pe.element.click()
        time.sleep(0.5)

        while 1:
            if self.isReachedPage(until, untilOr, empty, reload):
                break
            else:
                # print('>!> delay clicking "{}" button'.format(pe.text))
                self.browser.refresh()

    @catch.timeoutException
    def go(self, url,
           until: Union[Callable, Tuple[Callable, ...]] = None,
           untilOr: Tuple[Callable, ...] = None,
           empty: Callable = None, reload: Callable = None):
        self.config.url = url
        while 1:
            self.browser.get(url)
            time.sleep(1.0)
            self.wait.until(EC.url_contains(url))

            if self.isReachedPage(until, untilOr, empty, reload):
                break
            else:
                # print('>!> delay getting "{}"'.format(url))
                self.browser.refresh()

    def refresh(self,
                until: Union[Callable, Tuple[Callable, ...]] = None,
                untilOr: Tuple[Callable, ...] = None):
        while 1:
            self.browser.refresh()
            time.sleep(5.0)
            if CC.isReached(until, untilOr):
                break

    @property
    def currentUrl(self) -> str:
        return self.browser.current_url

    def getCookies(self) -> dict:
        return self.browser.get_cookies()

    def setCookies(self, cookies):
        for cookie in cookies:
            if 'expiry' in cookie:
                del cookie['expiry']
            self.browser.add_cookie(cookie)
