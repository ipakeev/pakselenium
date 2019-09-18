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


def sleepAfterGetPageDecorator(func):
    def wrapper(self, *args, **kwargs):
        res = func(self, *args, **kwargs)
        time.sleep(config.waitAfterGetUrl)
        return res

    return wrapper


def sleepAfterClickDecorator(func):
    def wrapper(self, *args, **kwargs):
        res = func(self, *args, **kwargs)
        time.sleep(config.waitAfterClick)
        return res

    return wrapper


def sleepAfterMoveCursorDecorator(func):
    def wrapper(self, *args, **kwargs):
        res = func(self, *args, **kwargs)
        time.sleep(config.waitAfterMoveCursor)
        return res

    return wrapper


def refreshOnExceptionDecorator(func):
    def wrapper(self, *args, **kwargs):
        while 1:
            try:
                res = func(self, *args, **kwargs)
                break
            except TimeoutException:
                self.refresh()
            except ElementNotVisibleException:
                self.refresh()
        return res

    return wrapper


class Status(object):
    browserName: str
    browserArgs: tuple
    timeout: int
    url: str
    chrome: str = 'chrome'
    firefox: str = 'firefox'
    phantomJS: str = 'phantomJS'


class Browser(object):
    browser: webdriver.Chrome
    wait: WebDriverWait
    actions: ActionChains
    status: Status
    selector: str = By.CSS_SELECTOR

    def __init__(self, timeout=10):
        self.status = Status()
        self.status.timeout = timeout

    def initChrome(self, driver: str):
        self.status.browserName = self.status.chrome
        self.status.browserArgs = (driver,)
        self.browser = webdriver.Chrome(driver)
        self.initAfterBrowser()

    def initFirefox(self, driver: str, binary: str):
        self.status.browserName = self.status.firefox
        self.status.browserArgs = (driver, binary)
        self.browser = webdriver.Firefox(firefox_binary=binary, executable_path=driver)
        self.initAfterBrowser()

    def initPhantomJS(self, driver: str):
        self.status.browserName = self.status.phantomJS
        self.status.browserArgs = (driver,)
        self.browser = webdriver.PhantomJS(executable_path=driver)
        self.initAfterBrowser()

    def initAfterBrowser(self):
        self.wait = WebDriverWait(self.browser, self.status.timeout)
        self.actions = ActionChains(self.browser)

    def newSession(self):
        assert self.status.browserName
        if self.status.browserName == self.status.chrome:
            self.initChrome(*self.status.browserArgs)
        elif self.status.browserName == self.status.firefox:
            self.initFirefox(*self.status.browserArgs)
        elif self.status.browserName == self.status.phantomJS:
            self.initPhantomJS(*self.status.browserArgs)
        else:
            raise StopIteration(self.status.browserName)

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

    def clearForm(self, element: WebElement):
        element.clear()

    def fillForm(self, element: WebElement, value: str):
        element.send_keys(value)

    def click(self, element: WebElement, wait=None, timeout=None):
        element.click()

    def moveCursor(self, element: WebElement):
        self.actions.reset_actions()
        self.actions.move_to_element(element)
        self.actions.perform()

    def refresh(self):
        self.browser.refresh()

    def getCookies(self):
        return self.browser.get_cookies()

    def setCookies(self, cookies):
        for cookie in cookies:
            self.browser.add_cookie(cookie)

    def isDisplayed(self, element: WebElement, wait=None):
        return element.is_displayed()

    def go(self, url, refresh=False, timeout=None):
        self.status.url = url
        self.browser.get(url)

    def addToDoOnNewSession(self, func, *args, **kwargs):
        pass

    def waitAvailable(self, waitAvailablePath, emptyPath=None, printer=True, timeout=None):
        pass


class BrowserOld(object):
    def __init__(self, browserName='chrome'):
        self.browserName = browserName
        self.browser = self._getBrowser(browserName)
        self.actions = ActionChains(self.browser)

        self._madeBrowserInstances = []
        self._doOnNewSession = []
        self._lastUrl = None

    def _getBrowser(self, browserName):
        self.browserName = browserName
        if browserName == 'chrome':
            browser = webdriver.Chrome(config.ChromeDriver)
        elif browserName == 'firefox':
            binary = FirefoxBinary(config.FirefoxBinary)
            browser = webdriver.Firefox(firefox_binary=binary, executable_path=config.FirefoxDriver)
        elif browserName == 'phantomJS':
            browser = webdriver.PhantomJS(executable_path=config.PhantomJSDriver)
        else:
            raise StopIteration(browserName)
        return browser

    def getBrowserWithFuncs(self, locator):
        inst = BrowserFuncs(browser=self, locator=locator)
        self._madeBrowserInstances.append(inst)
        return inst

    def addToDoOnNewSession(self, func, *args, **kwargs):
        self._doOnNewSession.append([func, args, kwargs])

    def newSession(self):
        self.close()
        self.browser = self._getBrowser(self.browserName)
        self.actions = ActionChains(self.browser)

        for inst in self._madeBrowserInstances:
            inst.setBrowser(self)

        for func, args, kwargs in self._doOnNewSession:
            func(*args, **kwargs)

    def close(self):
        try:
            self.browser.close()
        except Exception as e:
            print('<exception>: close: e = {}'.format(e))

    def exceptionCycle(self, func, *args, isCallable=True, printer=True, cycles=None, **kwargs):
        c = 0
        while 1:
            c += 1
            try:
                if isCallable:
                    res = func(*args, **kwargs)
                else:
                    res = func
                break
            except TimeoutException:
                # print('<exception>: {}: e = TimeoutException'.format(func.__name__))
                if cycles is not None and cycles == 1:
                    return None
                self.refresh()
            except CannotSendRequest:
                # print('<exception>: {}: e = CannotSendRequest'.format(func.__name__))
                pass
            except ElementNotVisibleException:
                # print('<exception>: {}: e = ElementNotVisibleException'.format(func.__name__))
                if cycles is not None and cycles == 1:
                    return None
                self.refresh()
            except ConnectionResetError:
                if printer:
                    print('<exception>: {}: e = ConnectionResetError'.format(func.__name__))
                return None
            except StaleElementReferenceException:
                if printer:
                    print('<exception>: {}: e = StaleElementReferenceException'.format(func.__name__))
                self.newSession()
                return 'retry'
            except InvalidElementStateException:
                if printer:
                    print('<exception>: {}: e = InvalidElementStateException'.format(func.__name__))
                self.newSession()
                return 'retry'
            except WebDriverException:
                if printer:
                    print('<exception>: {}: e = WebDriverException'.format(func.__name__))
                self.newSession()
                return 'retry'
            except Exception as e:
                if printer:
                    print('<exception>: {}: e = {}'.format(func.__name__, e))
                '''if cycles is not None:
                    assert isinstance(cycles, int)
                    if c >= cycles:
                        return None'''
                raise
        return res

    @staticmethod
    def _getWaitFunction(elementPath, locator='css'):
        if locator == 'xpath':
            func = lambda x: x.find_element_by_xpath(elementPath)
        elif locator == 'css':
            func = lambda x: x.find_element_by_css_selector(elementPath)
        else:
            raise StopIteration(locator)
        return func

    def _checkIsUrlBlocked(self):
        pass

    def _goToUrl(self, url, refresh=False, subUrl=None):
        if url is None:
            return
        self._lastUrl = url
        url = utils.makeUrlToGo(url)
        while 1:
            if self.exceptionCycle(self.browser.get, url) == 'retry':
                return 'retry'
            if refresh:
                self.refresh()

            time.sleep(config.waitAfterGetUrl)
            self._checkIsUrlBlocked()

            # на случай, если запросить self.browser.current_url при закрытом браузере
            try:
                achieved = self._isUrlAchieved(url, subUrl=subUrl)
            except WebDriverException:
                return 'retry'

            if achieved:
                return
            else:
                print('>!> Url not achieved!')

    def _isUrlAchieved(self, targetUrl, subUrl=None):
        targetUrl = utils.clearUrl(targetUrl)
        currentUrl = self.getCurrentUrl()
        if subUrl and subUrl in currentUrl:
            return True
        if currentUrl == targetUrl:
            return True
        # print('>!> urls: ', [currentUrl, targetUrl])
        return None

    @staticmethod
    def _getElement(elementPath, finder):
        if isinstance(elementPath, str):
            element = finder(elementPath)
        else:
            element = elementPath
        return element

    def _getIsEmptyPageFinder(self, emptyPath, locator='css'):
        if emptyPath is None:
            return
        finder = self.getFinderFunction(locator, oneElement=True)

        def isEmptyPage(printer=True):
            if isinstance(emptyPath, tuple) or isinstance(emptyPath, list):
                empty = []
                for path in emptyPath:
                    empty.append(self.getElementOne(path, locator=locator, finder=finder))
                if any(empty):
                    isEmpty = [i for i in empty if i][0]
                else:
                    isEmpty = None
            else:
                isEmpty = self.getElementOne(emptyPath, locator=locator, finder=finder)

            if type(isEmpty) is str and ('try again' in isEmpty or 'are no odds' in isEmpty):
                return None

            if isEmpty:
                if printer:
                    print('<msg>: {}'.format(isEmpty.text))
                return True

            return None

        return isEmptyPage

    def _getIsElementOnPageFinder(self, elementPath, locator='css'):
        if elementPath is None:
            return
        waitFunction = self._getWaitFunction(elementPath, locator=locator)

        def isElementOnPage(cycles=1, printer=True, timeout=None):
            timeout = config.webdriverWaitTimeOut if timeout is None else timeout
            func = WebDriverWait(self.browser, timeout).until
            element = self.exceptionCycle(func, waitFunction, cycles=cycles, printer=printer)
            if isinstance(element, WebElement) and element.is_enabled():
                return True
            return None

        return isElementOnPage

    def getFinderFunction(self, locator, oneElement=False):
        if locator == 'xpath':
            func = self.browser.find_element_by_xpath if oneElement \
                else self.browser.find_elements_by_xpath
        elif locator == 'css':
            func = self.browser.find_element_by_css_selector if oneElement \
                else self.browser.find_elements_by_css_selector
        else:
            raise StopIteration(locator)
        return func

    def isOnPage(self, elementPath, locator='css',
                 cycles=1, printer=True, timeout=None):
        isElementOnPage = self._getIsElementOnPageFinder(elementPath, locator=locator)
        return isElementOnPage(cycles=cycles, printer=printer, timeout=timeout)

    def isCurrentUrl(self, url):
        return self._isUrlAchieved(url)

    def getCurrentUrl(self):
        url = self.exceptionCycle(self.browser.current_url, isCallable=False)
        return utils.clearUrl(url)

    @sleepAfterGetPageDecorator
    def refresh(self):
        while self.exceptionCycle(self.browser.refresh) == 'retry':
            self._goToUrl(self._lastUrl)  # if browser closed

    @sleepAfterGetPageDecorator
    def getUrl(self, url, waitAvailablePath=None, emptyPath=None, locator='css', refresh=False, subUrl=None,
               cycles=1, printer=True, timeout=None):
        while 1:
            isEmptyPage = self._getIsEmptyPageFinder(emptyPath, locator=locator)
            isElementOnPage = self._getIsElementOnPageFinder(waitAvailablePath, locator=locator)

            if self._goToUrl(url, refresh=refresh, subUrl=subUrl) == 'retry':
                continue

            if emptyPath and isEmptyPage(printer=printer):
                return 'empty'
            if waitAvailablePath is None:
                return True
            if waitAvailablePath and isElementOnPage(cycles=cycles, printer=printer, timeout=timeout):
                return True

    def waitAvailable(self, waitAvailablePath, emptyPath=None, locator='css',
                      cycles=1, printer=True, timeout=None):
        isEmptyPage = self._getIsEmptyPageFinder(emptyPath, locator=locator)
        isElementOnPage = self._getIsElementOnPageFinder(waitAvailablePath, locator=locator)
        while 1:
            if emptyPath and isEmptyPage(printer=printer):
                return 'empty'
            if isElementOnPage(cycles=cycles, printer=printer, timeout=timeout):
                return True

    @sleepAfterClickDecorator
    @refreshOnExceptionDecorator
    def click(self, buttonPath, waitAvailablePath=None, emptyPath=None, locator='css', finder=None,
              cycles=1, printer=True, timeout=None):
        finder = finder or self.getFinderFunction(locator, oneElement=True)
        button = self._getElement(buttonPath, finder)
        button.click()
        if waitAvailablePath is None:
            return
        isEmptyPage = self._getIsEmptyPageFinder(emptyPath, locator=locator)
        isElementOnPage = self._getIsElementOnPageFinder(waitAvailablePath, locator=locator)
        while not isElementOnPage(cycles=cycles, printer=printer, timeout=timeout):
            if emptyPath and isEmptyPage(printer=printer):
                return 'empty'

    @sleepAfterClickDecorator
    @refreshOnExceptionDecorator
    def moveCursorAndClick(self, elementPath, hiddenPath, locator='css', finder=None):
        finder = finder or self.getFinderFunction(locator, oneElement=True)
        element = self._getElement(elementPath, finder)
        hidden = self._getElement(hiddenPath, finder)
        self.actions.reset_actions()
        self.actions.move_to_element(element)
        self.actions.click(hidden)
        self.actions.perform()

    @sleepAfterMoveCursorDecorator
    @refreshOnExceptionDecorator
    def moveCursor(self, elementPath, locator='css', finder=None):
        finder = finder or self.getFinderFunction(locator, oneElement=True)
        element = self._getElement(elementPath, finder)
        self.actions.reset_actions()
        self.actions.move_to_element(element)
        self.actions.perform()

    def clearForm(self, formPath, locator='css', finder=None):
        finder = finder or self.getFinderFunction(locator, oneElement=True)
        form = self._getElement(formPath, finder)
        form.clear()

    def fillForm(self, formPath, value, locator='css', finder=None):
        finder = finder or self.getFinderFunction(locator, oneElement=True)
        form = self._getElement(formPath, finder)
        form.send_keys(value)

    def getElementOne(self, elementPath, locator='css', finder=None):
        finder = finder or self.getFinderFunction(locator, oneElement=True)
        try:
            return finder(elementPath)
        except NoSuchElementException:
            return None

    def getTextOne(self, elementPath, locator='css', finder=None):
        element = self.getElementOne(elementPath, locator=locator, finder=finder)
        return element.text.strip() if element else None

    def getAttributeOne(self, elementPath, attribute, locator='css', finder=None):
        element = self.getElementOne(elementPath, locator=locator, finder=finder)
        return self.getAttributeFromElementOne(element, attribute)

    @staticmethod
    def getTextFromElementOne(element):
        return element.text.strip() if element else None

    @staticmethod
    def getAttributeFromElementOne(element, attribute):
        attr = element.get_attribute(attribute) if element else None
        if attr and attribute == 'href':
            attr = utils.clearUrl(attr)
        return attr

    def getElementAll(self, elementPath, locator='css', finder=None):
        finder = finder or self.getFinderFunction(locator)
        return finder(elementPath)

    def getTextAll(self, elementPath, locator='css', finder=None):
        element = self.getElementAll(elementPath, locator=locator, finder=finder)
        return [i.text.strip() for i in element]

    def getAttributeAll(self, elementPath, attribute, locator='css', finder=None):
        element = self.getElementAll(elementPath, locator=locator, finder=finder)
        return self.getAttributeFromElementAll(element, attribute)

    @staticmethod
    def getTextFromElementAll(element):
        return [i.text.strip() for i in element]

    @staticmethod
    def getAttributeFromElementAll(element, attribute):
        attr = [i.get_attribute(attribute) for i in element]
        if attribute == 'href':
            attr = [utils.clearUrl(i) for i in attr]
        return attr

    def getCookies(self):
        return self.browser.get_cookies()

    def addCookies(self, cookies):
        for cookie in cookies:
            self.browser.add_cookie(cookie)
