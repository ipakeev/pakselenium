import time
from functools import partial
from typing import List, Callable, Union, Tuple

import numpy as np
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from .utils import callable_conditions as CC
from .utils import catch
from .utils import expected_conditions as EC


class Selector:

    def __init__(self, by: str, value: str):
        self.by = by
        self.value = value

    def __repr__(self):
        return f"Selector('{self.by}', '{self.value}')"

    @property
    def locator(self) -> Tuple[str, str]:
        return self.by, self.value


class PageElement(object):
    element: WebElement
    text: str

    def __init__(self, element: WebElement):
        self.element = element
        self.text = self.element.text.strip()

    def is_displayed(self):
        return self.element.is_displayed()

    def get_attribute(self, name: str):
        return self.element.get_attribute(name)


class Config(object):
    driver_name: str
    driver_kwargs: dict
    timeout_wait: int = 20
    implicit_wait: int = 0
    url: str = ''
    chrome: str = 'chrome'
    firefox: str = 'firefox'
    phantomJS: str = 'phantomJS'


class Browser(object):
    driver: webdriver.Chrome
    driver_wait: WebDriverWait
    driver_actions: ActionChains
    config: Config

    def __init__(self, config: Config = None):
        self.config = config or Config()

    def init_chrome(self, driver_path: str, options: ChromeOptions = None):
        self.config.driver_name = self.config.chrome
        self.config.driver_kwargs = {
            'driver_path': driver_path,
            'options': options,
        }
        self.driver = webdriver.Chrome(executable_path=driver_path, options=options)
        self.init_after_browser()

    def init_firefox(self, driver_path: str, binary_path: str):
        self.config.driver_name = self.config.firefox
        self.config.driver_kwargs = {
            'driver_path': driver_path,
            'binary_path': binary_path,
        }
        self.driver = webdriver.Firefox(executable_path=driver_path, firefox_binary=FirefoxBinary(binary_path))
        self.init_after_browser()

    def init_phantomJS(self, driver_path: str):
        self.config.driver_name = self.config.phantomJS
        self.config.driver_kwargs = {
            'driver_path': driver_path,
        }
        self.driver = webdriver.PhantomJS(executable_path=driver_path)
        self.init_after_browser()

    def init_after_browser(self):
        self.driver.implicitly_wait(self.config.implicit_wait)
        self.driver_wait = WebDriverWait(self.driver, self.config.timeout_wait)
        self.driver_actions = ActionChains(self.driver)
        time.sleep(1.0)

    def new_session(self):
        assert self.config.driver_name
        self.close()
        if self.config.driver_name == self.config.chrome:
            self.init_chrome(**self.config.driver_kwargs)
        elif self.config.driver_name == self.config.firefox:
            self.init_firefox(**self.config.driver_kwargs)
        elif self.config.driver_name == self.config.phantomJS:
            self.init_phantomJS(**self.config.driver_kwargs)
        else:
            raise StopIteration(self.config.driver_name)

    def close(self):
        try:
            self.driver.close()
        except WebDriverException:
            pass

    def is_on_page(self, selector: Selector) -> bool:
        try:
            self.driver.find_element(selector.by, selector.value)
            return True
        except NoSuchElementException:
            return False

    @catch.staleElementReferenceException()
    def find_element(self, selector: Selector) -> PageElement:
        if not self.is_on_page(selector):
            raise NoSuchElementException
        element = self.driver.find_element(selector.by, selector.value)
        return PageElement(element)

    @catch.staleElementReferenceException()
    def find_elements(self, selector: Selector) -> List[PageElement]:
        if not self.is_on_page(selector):
            raise NoSuchElementException
        es = self.driver.find_elements(selector.by, selector.value)
        pes = []
        for element in es:
            pes.append(PageElement(element))
        return pes

    @catch.staleElementReferenceException()
    def find_elements_with_text(self, selector: Selector, element_text: str) -> List[PageElement]:
        pe = self.find_elements(selector)
        es = [i for i in pe if i.text == element_text]
        if not es:
            raise NoSuchElementException
        return es

    @catch.staleElementReferenceException()
    def find_elements_contains(self, selector: Selector, element_text: str) -> List[PageElement]:
        pe = self.find_elements(selector)
        es = [i for i in pe if element_text in i.text]
        if not es:
            raise NoSuchElementException
        return es

    @catch.staleElementReferenceException()
    def find_element_from(self, pe: PageElement, selector: Selector) -> PageElement:
        element = pe.element.find_element(selector.by, selector.value)
        return PageElement(element)

    @catch.staleElementReferenceException()
    def find_elements_from(self, pe: PageElement, selector: Selector) -> List[PageElement]:
        es = pe.element.find_elements(selector.by, selector.value)
        pes = []
        for element in es:
            pes.append(PageElement(element))
        return pes

    @catch.staleElementReferenceException()
    def find_element_with_text_from(self, pe: PageElement, selector: Selector, text: str) -> PageElement:
        pe = self.find_elements_from(pe, selector)
        es = [i for i in pe if i.text == text]
        if not es:
            raise NoSuchElementException
        return es[0]

    def get_page_element(self, selector: Union[Selector, PageElement], element_text: str = None,
                         element_index: int = None) -> PageElement:
        if isinstance(selector, Selector):
            element_index = 0 if element_index is None else element_index
            if element_text:
                return self.find_elements_with_text(selector, element_text)[element_index]
            else:
                if element_index == 0:
                    return self.find_element(selector)
                else:
                    return self.find_elements(selector)[element_index]
        elif isinstance(selector, PageElement):
            assert element_text is None
            assert element_index is None
            return selector
        else:
            raise StopIteration

    def get_is_on_page_callable(self, selector: Selector) -> Callable:
        return lambda: self.is_on_page(selector)

    def get_is_not_on_page_callable(self, selector: Selector) -> Callable:
        return lambda: not self.is_on_page(selector)

    def wait_until_on_page(self, selector: Union[Selector, List[Selector]], forever: bool = False):
        if isinstance(selector, Selector):
            func = self.get_is_on_page_callable(selector)
        else:
            func = [self.get_is_on_page_callable(i) for i in selector]
        self.wait_until(func, forever=forever)

    def wait_until_not_on_page(self, selector: Union[Selector, List[Selector]], forever: bool = False):
        if isinstance(selector, Selector):
            func = self.get_is_not_on_page_callable(selector)
        else:
            func = [self.get_is_not_on_page_callable(i) for i in selector]
        self.wait_until(func, forever=forever)

    def wait_until_selector(self, EC_condition: Callable,
                            selector: Union[Selector, List[Selector]], *args, forever: bool = False, **kwargs):
        if isinstance(selector, Selector):
            func = partial(EC_condition(selector.locator, *args, **kwargs), self.driver)
        else:
            func = [partial(EC_condition(i.locator, *args, **kwargs), self.driver) for i in selector]
        self.wait_until(func, forever=forever)

    def wait_until_not_selector(self, EC_condition: Callable,
                                selector: Union[Selector, List[Selector]], *args, forever: bool = False, **kwargs):
        if isinstance(selector, Selector):
            func = partial(EC_condition(selector.locator, *args, **kwargs), self.driver)
        else:
            func = [partial(EC_condition(i.locator, *args, **kwargs), self.driver) for i in selector]
        self.wait_until_not(func, forever=forever)

    def wait_until_page_element(self, EC_condition: Callable,
                                pe: Union[PageElement, List[PageElement]], *args, forever: bool = False, **kwargs):
        if isinstance(pe, PageElement):
            func = partial(EC_condition(pe.element, *args, **kwargs), self.driver)
        else:
            func = [partial(EC_condition(i.element, *args, **kwargs), self.driver) for i in pe]
        self.wait_until(func, forever=forever)

    def wait_until_not_page_element(self, EC_condition: Callable,
                                    pe: Union[PageElement, List[PageElement]], *args, forever: bool = False, **kwargs):
        if isinstance(pe, PageElement):
            func = partial(EC_condition(pe.element, *args, **kwargs), self.driver)
        else:
            func = [partial(EC_condition(i.element, *args, **kwargs), self.driver) for i in pe]
        self.wait_until_not(func, forever=forever)

    def wait_until(self, func: Union[Callable, List[Callable]], forever: bool = False):
        if type(func) is list:
            until = lambda driver: all([i() for i in func])
        else:
            until = lambda driver: func()

        while 1:
            try:
                self.driver_wait.until(until)
                break
            except TimeoutException as e:
                if not forever:
                    raise e

    def wait_until_not(self, func: Union[Callable, List[Callable]], forever: bool = False):
        if type(func) is list:
            until = lambda driver: all([not i() for i in func])
        else:
            until = lambda driver: not func()

        while 1:
            try:
                self.driver_wait.until(until)
                break
            except TimeoutException as e:
                if not forever:
                    raise e

    def _get_callable_until(self, until: Union[Selector, List[Selector], Callable, List[Callable]]
                            ) -> Union[Callable, List[Callable]]:
        if until is None:
            pass
        elif isinstance(until, Selector):
            until = self.get_is_on_page_callable(until)
        elif callable(until):
            pass
        elif isinstance(until[0], Selector):
            until = [self.get_is_on_page_callable(i) for i in until]
        elif callable(until[0]):
            pass
        else:
            raise StopIteration
        return until

    def _get_callable_until_lost(self, until_lost: Union[Selector, List[Selector]]) -> Union[Callable, List[Callable]]:
        if until_lost is None:
            pass
        elif isinstance(until_lost, Selector):
            until_lost = self.get_is_not_on_page_callable(until_lost)
        elif isinstance(until_lost, list):
            until_lost = [self.get_is_not_on_page_callable(i) for i in until_lost]
        else:
            raise StopIteration
        return until_lost

    def is_reached_page(self, until: Union[Selector, List[Selector], Callable, List[Callable]],
                        until_lost: Union[Selector, List[Selector]], empty: Callable, reload: Callable) -> bool:
        until = self._get_callable_until(until)
        until_lost = self._get_callable_until_lost(until_lost)
        tt = time.time()
        while 1:
            if CC.is_empty(empty):
                return True
            if CC.is_reload(reload):
                self.driver.refresh()
                continue
            if CC.is_reached(until) and CC.is_reached(until_lost):
                return True
            if time.time() - tt >= self.config.timeout_wait:
                return False
            time.sleep(0.5)

    @catch.timeoutException()
    def go(self, url: str,
           until: Union[Selector, List[Selector], Callable, List[Callable]] = None,
           until_lost: Union[Selector, List[Selector]] = None,
           empty: Callable = None, reload: Callable = None, is_reached_url: Callable = None, sleep: float = 1.0):
        self.config.url = url
        while 1:
            self.driver.get(url)
            time.sleep(sleep)

            if callable(is_reached_url):
                self.wait_until(partial(is_reached_url(url), self.driver))

            if self.is_reached_page(until, until_lost, empty, reload):
                break
            else:
                # print('>!> delay getting "{}"'.format(url))
                self.driver.refresh()

    @catch.timeoutException()
    @catch.staleElementReferenceException()
    def click(self, selector: Union[Selector, PageElement], element_text: str = None, element_index: int = None,
              until: Union[Selector, List[Selector], Callable, List[Callable]] = None,
              until_lost: Union[Selector, List[Selector]] = None,
              empty: Callable = None, reload: Callable = None, sleep: float = 0.5):
        if isinstance(selector, Selector):
            self.wait_until_selector(EC.element_to_be_clickable, selector)
        pe = self.get_page_element(selector, element_text=element_text, element_index=element_index)
        pe.element.click()
        time.sleep(sleep)

        if not self.is_reached_page(until, until_lost, empty, reload):
            raise StaleElementReferenceException

    def refresh(self, until: Union[Selector, List[Selector], Callable, List[Callable]] = None, sleep: float = 5.0):
        until = self._get_callable_until(until)
        while 1:
            self.driver.refresh()
            time.sleep(sleep)
            if CC.is_reached(until):
                break

    @property
    def current_url(self) -> str:
        return self.driver.current_url

    def get_cookies(self) -> dict:
        return self.driver.get_cookies()

    def set_cookies(self, cookies):
        for cookie in cookies:
            if 'expiry' in cookie:
                del cookie['expiry']
            self.driver.add_cookie(cookie)

    @catch.staleElementReferenceException()
    def select(self, selector: Union[Selector, PageElement], element_text: str = None, element_index: int = None,
               sleep: float = 0.5):
        if isinstance(selector, Selector):
            self.wait_until_selector(EC.element_to_be_clickable, selector)
        pe = self.get_page_element(selector, element_text=element_text, element_index=element_index)
        assert not pe.element.is_selected()
        pe.element.click()
        self.wait_until_page_element(EC.is_selected, pe)
        time.sleep(sleep)

    @catch.staleElementReferenceException()
    def deselect(self, selector: Union[Selector, PageElement], element_text: str = None, element_index: int = None,
                 sleep: float = 0.5):
        if isinstance(selector, Selector):
            self.wait_until_selector(EC.element_to_be_clickable, selector)
        pe = self.get_page_element(selector, element_text=element_text, element_index=element_index)
        assert pe.element.is_selected()
        pe.element.click()
        self.wait_until_not_page_element(EC.is_selected, pe)
        time.sleep(sleep)

    def fill_text(self, selector: Union[Selector, PageElement], text: str, element_index: int = None,
                  clear: bool = True, quick: bool = False, sleep: float = 0.5):
        if isinstance(selector, Selector):
            self.wait_until_selector(EC.element_to_be_clickable, selector)
        pe = self.get_page_element(selector, element_index=element_index)
        if clear:
            pe.element.clear()

        if quick:
            pe.element.send_keys(text)
        else:
            for s in text:
                pe.element.send_keys(s)
                time.sleep(np.random.random() / 5)

        time.sleep(sleep)

    def fill_text_one_by_one(self, selector: Selector, texts: List[str], check_length: bool = True,
                             quick: bool = False, sleep: float = 0.5):
        self.wait_until_selector(EC.element_to_be_clickable, selector)
        pes = self.find_elements(selector)
        if check_length:
            assert len(pes) == len(texts)

        for pe, text in zip(pes, texts):
            pe.element.clear()
            pe.element.send_keys(text)
            if not quick:
                time.sleep(np.random.random() / 5)

        time.sleep(sleep)

    def move_cursor(self, selector: Union[Selector, PageElement], element_text: str = None, element_index: int = None,
                    sleep: float = 0.5):
        if isinstance(selector, Selector):
            self.wait_until_selector(EC.element_to_be_clickable, selector)
        pe = self.get_page_element(selector, element_text=element_text, element_index=element_index)
        self.driver_actions.reset_actions()
        self.driver_actions.move_to_element(pe.element)
        self.driver_actions.perform()
        time.sleep(sleep)

    def drug_and_drop(self, source: Union[Selector, PageElement], target: Union[Selector, PageElement],
                      source_text: str = None, target_text: str = None,
                      source_index: int = None, target_index: int = None,
                      sleep: float = 0.5):
        if isinstance(source, Selector):
            self.wait_until_selector(EC.element_to_be_clickable, source)
        if isinstance(target, Selector):
            self.wait_until_selector(EC.element_to_be_clickable, target)
        source = self.get_page_element(source, element_text=source_text, element_index=source_index)
        target = self.get_page_element(target, element_text=target_text, element_index=target_index)
        self.driver_actions.reset_actions()
        self.driver_actions.drag_and_drop(source, target).perform()
        time.sleep(sleep)

    def press_key(self, key):
        self.driver_actions.reset_actions()
        self.driver_actions.key_down(key).key_up(key).perform()

    def press_Enter(self):
        self.press_key(Keys.ENTER)

    def press_Backspace(self):
        self.press_key(Keys.BACKSPACE)

    def press_Tab(self):
        self.press_key(Keys.TAB)

    def press_Esc(self):
        self.press_key(Keys.ESCAPE)
