import random
import time
from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import List, Callable, Union, Tuple, Optional

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from pakselenium import config
from pakselenium.utils import callable_conditions as CC
from pakselenium.utils import catch
from pakselenium.utils import expected_conditions as EC


class Selector:

    def __init__(self, by: str, value: str, desc: str = None):
        self.by = by
        self.value = value
        self.desc = desc

    def __repr__(self):
        if self.desc:
            return f"Selector('{self.desc}')"
        else:
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

    def __repr__(self):
        return f"PageElement('{self.text}')"

    def is_displayed(self):
        return self.element.is_displayed()

    def get_attribute(self, name: str):
        return self.element.get_attribute(name)


class Names(Enum):
    chrome = 'chrome'
    firefox = 'firefox'
    phantomJS = 'phantomJS'


@dataclass
class Settings(object):
    driver_name: str = None
    driver_kwargs: dict = None
    timeout_wait: int = 20
    implicit_wait: int = 0
    url: str = ''


def log(msg: Optional[str], min_verbose: int = 2, end=None):
    if msg and config.debug_verbose >= min_verbose:
        print(msg, end=end)


class Browser(object):
    driver: webdriver.Chrome
    driver_wait: WebDriverWait
    driver_actions: ActionChains
    wait_page_loading: bool = True
    stop_page_loading: Callable

    def __init__(self):
        self.settings = Settings()

    def init_chrome(self,
                    driver_path: str,
                    options: ChromeOptions = None,
                    wait_page_loading=True,
                    **kwargs):
        self.settings.driver_name = Names.chrome.value
        self.settings.driver_kwargs = dict(driver_path=driver_path, options=options,
                                           wait_page_loading=wait_page_loading, **kwargs)
        self.wait_page_loading = wait_page_loading
        self.stop_page_loading = lambda: self.driver.execute_script("window.stop();")
        if not wait_page_loading:
            capa = DesiredCapabilities.CHROME
            capa['pageLoadStrategy'] = 'none'
        else:
            capa = None

        self.driver = webdriver.Chrome(executable_path=driver_path,
                                       options=options,
                                       desired_capabilities=capa,
                                       **kwargs)
        self.init_after_browser()

    def init_firefox(self,
                     driver_path: str,
                     binary_path: str,
                     **kwargs):
        self.settings.driver_name = Names.firefox.value
        self.settings.driver_kwargs = dict(driver_path=driver_path, binary_path=binary_path, **kwargs)
        self.driver = webdriver.Firefox(executable_path=driver_path,
                                        firefox_binary=FirefoxBinary(binary_path),
                                        **kwargs)
        self.init_after_browser()

    def init_phantomJS(self,
                       driver_path: str,
                       **kwargs):
        self.settings.driver_name = Names.phantomJS.value
        self.settings.driver_kwargs = dict(driver_path=driver_path, **kwargs)
        self.driver = webdriver.PhantomJS(executable_path=driver_path, **kwargs)
        self.init_after_browser()

    def init_after_browser(self):
        self.driver.implicitly_wait(self.settings.implicit_wait)
        self.driver_wait = WebDriverWait(self.driver, self.settings.timeout_wait)
        self.driver_actions = ActionChains(self.driver)
        time.sleep(1.0)

    def new_session(self):
        assert self.settings.driver_name
        self.close()
        if self.settings.driver_name == Names.chrome.value:
            self.init_chrome(**self.settings.driver_kwargs)
        elif self.settings.driver_name == Names.firefox.value:
            self.init_firefox(**self.settings.driver_kwargs)
        elif self.settings.driver_name == Names.phantomJS.value:
            self.init_phantomJS(**self.settings.driver_kwargs)
        else:
            raise StopIteration(self.settings.driver_name)

    def close(self):
        try:
            self.driver.close()
        except WebDriverException:
            pass

    def is_on_page(self, selector: Selector, desc: str = None) -> bool:
        log(f'[is_on_page]: {desc}: {selector.desc}' if desc else None, end=' ... ')
        try:
            self.driver.find_element(selector.by, selector.value)
            log(f'[True]' if desc else None)
            return True
        except NoSuchElementException:
            log(f'[False]' if desc else None)
            return False

    @catch.staleElementReferenceException()
    def find_element(self, selector: Selector, desc: str = None) -> PageElement:
        log(f'[find_element]: {desc}: {selector.desc}' if desc else None, end=' ... ')
        if not self.is_on_page(selector):
            raise NoSuchElementException
        element = self.driver.find_element(selector.by, selector.value)
        pe = PageElement(element)
        log(f'found {pe}' if desc else None)
        return pe

    @catch.staleElementReferenceException()
    def find_elements(self, selector: Selector, desc: str = None) -> List[PageElement]:
        log(f'[find_elements]: {desc}: {selector.desc}' if desc else None, end=' ... ')
        if not self.is_on_page(selector):
            raise NoSuchElementException
        es = self.driver.find_elements(selector.by, selector.value)
        pes = []
        for element in es:
            pes.append(PageElement(element))
        log(f'found {pes}' if desc else None)
        return pes

    @catch.staleElementReferenceException()
    def find_elements_with_text(self, selector: Selector, element_text: str, desc: str = None) -> List[PageElement]:
        log(f'[find_elements_with_text]: {desc}: {selector.desc} with "{element_text}"' if desc else None, end=' ... ')
        pe = self.find_elements(selector)
        es = [i for i in pe if i.text == element_text]
        if not es:
            raise NoSuchElementException
        log(f'found {es}' if desc else None)
        return es

    @catch.staleElementReferenceException()
    def find_elements_contains(self, selector: Selector, element_text: str, desc: str = None) -> List[PageElement]:
        log(f'[find_elements_contains]: {desc}: {selector.desc} contains "{element_text}"' if desc else None,
            end=' ... ')
        pe = self.find_elements(selector)
        es = [i for i in pe if element_text in i.text]
        if not es:
            raise NoSuchElementException
        log(f'found {es}' if desc else None)
        return es

    @catch.staleElementReferenceException()
    def find_element_from(self, from_pe: PageElement, selector: Selector, desc: str = None) -> PageElement:
        log(f'[find_element_from]: {desc}: {selector.desc} from {from_pe.text}' if desc else None, end=' ... ')
        element = from_pe.element.find_element(selector.by, selector.value)
        pe = PageElement(element)
        log(f'found {pe}' if desc else None)
        return pe

    @catch.staleElementReferenceException()
    def find_elements_from(self, from_pe: PageElement, selector: Selector, desc: str = None) -> List[PageElement]:
        log(f'[find_elements_from]: {desc}: {selector.desc} from {from_pe.text}' if desc else None, end=' ... ')
        es = from_pe.element.find_elements(selector.by, selector.value)
        pes = []
        for element in es:
            pes.append(PageElement(element))
        log(f'found {pes}' if desc else None)
        return pes

    @catch.staleElementReferenceException()
    def find_element_with_text_from(self, from_pe: PageElement, selector: Selector, text: str,
                                    desc: str = None) -> PageElement:
        log(f'[find_elements_from]: {desc}: {selector.desc} from {from_pe.text}' if desc else None, end=' ... ')
        pe = self.find_elements_from(from_pe, selector)
        pes = [i for i in pe if i.text == text]
        if not pes:
            raise NoSuchElementException
        log(f'found {pes}' if desc else None)
        return pes[0]

    def get_page_element(self, selector: Union[Selector, PageElement], element_text: str = None,
                         element_index: int = None, desc: str = None) -> PageElement:
        if isinstance(selector, Selector):
            element_index = 0 if element_index is None else element_index
            if element_text:
                return self.find_elements_with_text(selector, element_text, desc=desc)[element_index]
            else:
                if element_index == 0:
                    return self.find_element(selector, desc=desc)
                else:
                    return self.find_elements(selector, desc=desc)[element_index]
        elif isinstance(selector, PageElement):
            assert element_text is None
            assert element_index is None
            return selector
        else:
            raise StopIteration

    def get_is_on_page_callable(self, selector: Selector, desc: str = None) -> Callable:
        return lambda: self.is_on_page(selector, desc=desc)

    def get_is_not_on_page_callable(self, selector: Selector, desc: str = None) -> Callable:
        return lambda: not self.is_on_page(selector, desc=desc)

    def wait_until_on_page(self, selector: Union[Selector, List[Selector]],
                           forever: bool = False, desc: str = None, timeout: int = None):
        if isinstance(selector, Selector):
            func = self.get_is_on_page_callable(selector, desc=desc)
        else:
            func = [self.get_is_on_page_callable(i, desc=desc) for i in selector]
        self.wait_until(func, forever=forever, timeout=timeout)

    def wait_until_not_on_page(self, selector: Union[Selector, List[Selector]],
                               forever: bool = False, desc: str = None, timeout: int = None):
        if isinstance(selector, Selector):
            func = self.get_is_not_on_page_callable(selector, desc=desc)
        else:
            func = [self.get_is_not_on_page_callable(i, desc=desc) for i in selector]
        self.wait_until(func, forever=forever, timeout=timeout)

    def wait_until_selector(self, EC_condition: Callable,
                            selector: Union[Selector, List[Selector]], *args,
                            forever: bool = False, desc: str = None, timeout: int = None, **kwargs):
        if isinstance(selector, Selector):
            func = partial(EC_condition(selector.locator, *args, **kwargs), self.driver)
        else:
            func = [partial(EC_condition(i.locator, *args, **kwargs), self.driver) for i in selector]
        self.wait_until(func, forever=forever, desc=desc, timeout=timeout)

    def wait_until_not_selector(self, EC_condition: Callable,
                                selector: Union[Selector, List[Selector]], *args,
                                forever: bool = False, desc: str = None, timeout: int = None, **kwargs):
        if isinstance(selector, Selector):
            func = partial(EC_condition(selector.locator, *args, **kwargs), self.driver)
        else:
            func = [partial(EC_condition(i.locator, *args, **kwargs), self.driver) for i in selector]
        self.wait_until_not(func, forever=forever, desc=desc, timeout=timeout)

    def wait_until_page_element(self, EC_condition: Callable,
                                pe: Union[PageElement, List[PageElement]], *args,
                                forever: bool = False, desc: str = None, timeout: int = None, **kwargs):
        if isinstance(pe, PageElement):
            func = partial(EC_condition(pe.element, *args, **kwargs), self.driver)
        else:
            func = [partial(EC_condition(i.element, *args, **kwargs), self.driver) for i in pe]
        self.wait_until(func, forever=forever, desc=desc, timeout=timeout)

    def wait_until_not_page_element(self, EC_condition: Callable,
                                    pe: Union[PageElement, List[PageElement]], *args,
                                    forever: bool = False, desc: str = None, timeout: int = None, **kwargs):
        if isinstance(pe, PageElement):
            func = partial(EC_condition(pe.element, *args, **kwargs), self.driver)
        else:
            func = [partial(EC_condition(i.element, *args, **kwargs), self.driver) for i in pe]
        self.wait_until_not(func, forever=forever, desc=desc, timeout=timeout)

    def wait_until(self, func: Union[Callable, List[Callable]], forever: bool = False, desc: str = None,
                   timeout: int = None):
        log(f'[wait_until]: {desc}' if desc else None, end=' ... ')
        if timeout is not None:
            self.driver_wait._timeout = timeout

        if type(func) is list:
            until = lambda driver: all([i() for i in func])
        else:
            until = lambda driver: func()

        while 1:
            try:
                self.driver_wait.until(until)
                break
            except TimeoutException as e:
                log(f'[wait_until]: {desc} caught TimeoutException', 1)
                if not forever:
                    raise e

        self.driver_wait._timeout = self.settings.timeout_wait
        log(f'done' if desc else None)

    def wait_until_not(self, func: Union[Callable, List[Callable]], forever: bool = False, desc: str = None,
                       timeout: int = None):
        log(f'[wait_until_not]: {desc}' if desc else None, end=' ... ')
        if timeout is not None:
            self.driver_wait._timeout = timeout

        if type(func) is list:
            until = lambda driver: all([not i() for i in func])
        else:
            until = lambda driver: not func()

        while 1:
            try:
                self.driver_wait.until(until)
                break
            except TimeoutException as e:
                log(f'[wait_until]: {desc} caught TimeoutException', 1)
                if not forever:
                    raise e

        self.driver_wait._timeout = self.settings.timeout_wait
        log(f'done' if desc else None)

    def _get_callable_until(self, until: Union[Selector, List[Selector],
                                               Callable, List[Callable]]) -> Union[Callable, List[Callable]]:
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

    def condition_text_is_in(self, selector: Selector, text: str, desc: str = None) -> bool:
        if self.is_on_page(selector):
            found = self.find_element(selector).text
            if text in found:
                log(f'[condition_text_is_in:True]: {desc}: "{text}" in {found}' if desc else None)
                return True
            else:
                log(f'[condition_text_is_in:False]: {desc}: "{text}" not in {found}' if desc else None)
                return False
        log(f'[condition_text_is_in:False]: {desc}: "{text}" not in {selector}' if desc else None)
        return False

    def condition_text_not_in(self, selector: Selector, text: str, desc: str = None) -> bool:
        if self.is_on_page(selector):
            found = self.find_element(selector).text
            if text not in found:
                log(f'[condition_text_not_in:True]: {desc}: "{text}" not in {found}' if desc else None)
                return True
            else:
                log(f'[condition_text_not_in:False]: {desc}: "{text}" in {found}' if desc else None)
                return False
        log(f'[condition_text_not_in:False]: {desc}: "{text}" in {selector}' if desc else None)
        return False

    def condition_text_equal(self, selector: Selector, text: str, desc: str = None) -> bool:
        if self.is_on_page(selector):
            found = self.find_element(selector).text
            if text == found:
                log(f'[condition_text_equal:True]: {desc}: "{text}" == {found}' if desc else None)
                return True
            else:
                log(f'[condition_text_equal:False]: {desc}: "{text}" != {found}' if desc else None)
                return False
        log(f'[condition_text_equal:False]: {desc}: "{text}" != {selector}' if desc else None)
        return False

    def condition_text_not_equal(self, selector: Selector, text: str, desc: str = None) -> bool:
        if self.is_on_page(selector):
            found = self.find_element(selector).text
            if text != found:
                log(f'[condition_text_not_equal:True]: {desc}: "{text}" != {found}' if desc else None)
                return True
            else:
                log(f'[condition_text_not_equal:False]: {desc}: "{text}" == {found}' if desc else None)
                return False
        log(f'[condition_text_not_equal:False]: {desc}: "{text}" == {selector}' if desc else None)
        return False

    def is_reached_page(self, until: Union[Selector, List[Selector], Callable, List[Callable]],
                        until_lost: Union[Selector, List[Selector]], empty: Callable, reload: Callable,
                        desc: str = None, timeout: int = None) -> bool:
        until = self._get_callable_until(until)
        until_lost = self._get_callable_until_lost(until_lost)
        tt = time.time()
        timeout = self.settings.timeout_wait if timeout is None else timeout
        while 1:
            log(f'[is_reached_page]: {desc}' if desc else None)
            if CC.is_empty(empty):
                return True
            if CC.is_reload(reload):
                if not self.wait_page_loading:
                    self.stop_page_loading()
                self.driver.refresh()
                continue
            if CC.is_reached(until) and CC.is_reached(until_lost):
                return True
            if time.time() - tt >= timeout:
                return False
            time.sleep(0.5)
        log(f'[is_reached_page]: done' if desc else None)

    def go(self, url: str,
           until: Union[Selector, List[Selector], Callable, List[Callable]] = None,
           until_lost: Union[Selector, List[Selector]] = None,
           empty: Callable = None, reload: Callable = None, is_reached_url: Callable = None, sleep: float = 1.0,
           desc: str = None, timeout: int = None):
        self.settings.url = url
        while 1:
            log(f'[go:"{url}"]: {desc}' if desc else None)
            self.driver.get(url)
            time.sleep(sleep)

            if callable(is_reached_url):
                self.wait_until(partial(is_reached_url(url), self.driver), timeout=timeout)

            if self.is_reached_page(until, until_lost, empty, reload, desc=f'[go:waiting]', timeout=timeout):
                if not self.wait_page_loading:
                    self.stop_page_loading()
                break
            else:
                if not self.wait_page_loading:
                    self.stop_page_loading()
                log(f'[go:refresh:"{url}"]: {desc}' if desc else None)
                self.driver.refresh()
                time.sleep(sleep)
                if not self.wait_page_loading:
                    self.stop_page_loading()

        if not self.wait_page_loading:
            self.stop_page_loading()
        log(f'[go]: done' if desc else None)

    def click(self, selector: Union[Selector, PageElement], element_text: str = None, element_index: int = None,
              until: Union[Selector, List[Selector], Callable, List[Callable]] = None,
              until_lost: Union[Selector, List[Selector]] = None,
              empty: Callable = None, reload: Callable = None,
              sleep: float = 0.5, desc: str = None, timeout: int = None):
        log(f'[click:{selector}[{element_text}, {element_index}]]: {desc}' if desc else None)
        if isinstance(selector, Selector):
            self.wait_until_selector(EC.element_to_be_clickable, selector, timeout=timeout)
        pe = self.get_page_element(selector, element_text=element_text, element_index=element_index)
        pe.element.click()
        time.sleep(sleep)

        self.wait_until(lambda: self.is_reached_page(until, until_lost, empty, reload),
                        desc=f'[click:waiting]', timeout=timeout)
        if not self.wait_page_loading:
            self.stop_page_loading()

    def refresh(self, until: Union[Selector, List[Selector], Callable, List[Callable]] = None, sleep: float = 5.0,
                desc: str = None):
        log(f'[refresh]: {desc}' if desc else None, end=' ... ')
        until = self._get_callable_until(until)
        while 1:
            self.driver.refresh()
            time.sleep(sleep)
            if CC.is_reached(until):
                break
            if not self.wait_page_loading:
                self.stop_page_loading()

        if not self.wait_page_loading:
            self.stop_page_loading()
        log(f'done' if desc else None)

    @property
    def current_url(self) -> str:
        return self.driver.current_url

    def get_cookies(self, desc: str = None) -> dict:
        log(f'[get_cookies]: {desc}' if desc else None)
        return self.driver.get_cookies()

    def set_cookies(self, cookies, desc: str = None):
        log(f'[set_cookies]: {desc}' if desc else None)
        for cookie in cookies:
            if 'expiry' in cookie:
                del cookie['expiry']
            self.driver.add_cookie(cookie)

    @catch.staleElementReferenceException()
    def select(self, selector: Union[Selector, PageElement], element_text: str = None, element_index: int = None,
               sleep: float = 0.5, desc: str = None):
        log(f'[select:{selector}[{element_text}, {element_index}]]: {desc}' if desc else None, end=' ... ')
        if isinstance(selector, Selector):
            self.wait_until_selector(EC.element_to_be_clickable, selector)
        pe = self.get_page_element(selector, element_text=element_text, element_index=element_index)
        assert not pe.element.is_selected()
        pe.element.click()
        self.wait_until_page_element(EC.is_selected, pe)
        time.sleep(sleep)
        log(f'done' if desc else None)

    @catch.staleElementReferenceException()
    def deselect(self, selector: Union[Selector, PageElement], element_text: str = None, element_index: int = None,
                 sleep: float = 0.5, desc: str = None):
        log(f'[deselect:{selector}[{element_text}, {element_index}]]: {desc}' if desc else None, end=' ... ')
        if isinstance(selector, Selector):
            self.wait_until_selector(EC.element_to_be_clickable, selector)
        pe = self.get_page_element(selector, element_text=element_text, element_index=element_index)
        assert pe.element.is_selected()
        pe.element.click()
        self.wait_until_not_page_element(EC.is_selected, pe)
        time.sleep(sleep)
        log(f'done' if desc else None)

    def fill_text(self, selector: Union[Selector, PageElement], text: str, element_index: int = None,
                  clear: bool = True, quick: bool = False, sleep: float = 0.5, desc: str = None):
        log(f'[fill_text:{selector}={text}]: {desc}' if desc else None, end=' ... ')
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
                time.sleep(random.random() / 10)

        time.sleep(sleep)
        log(f'done' if desc else None)

    def fill_text_one_by_one(self, selector: Selector, texts: List[str], check_length: bool = True,
                             quick: bool = False, sleep: float = 0.5, desc: str = None):
        log(f'[fill_text_one_by_one:{selector}={texts}]: {desc}' if desc else None, end=' ... ')
        self.wait_until_selector(EC.element_to_be_clickable, selector)
        pes = self.find_elements(selector)
        if check_length:
            assert len(pes) == len(texts)

        for pe, text in zip(pes, texts):
            pe.element.clear()
            pe.element.send_keys(text)
            if not quick:
                time.sleep(random.random() / 5)

        time.sleep(sleep)
        log(f'done' if desc else None)

    def move_cursor(self, selector: Union[Selector, PageElement], element_text: str = None, element_index: int = None,
                    sleep: float = 0.5, desc: str = None):
        log(f'[move_cursor:{selector}]: {desc}' if desc else None, end=' ... ')
        if isinstance(selector, Selector):
            self.wait_until_selector(EC.element_to_be_clickable, selector)
        pe = self.get_page_element(selector, element_text=element_text, element_index=element_index)
        self.driver_actions.reset_actions()
        self.driver_actions.move_to_element(pe.element)
        self.driver_actions.perform()
        time.sleep(sleep)
        log(f'done' if desc else None)

    def drug_and_drop(self, source: Union[Selector, PageElement], target: Union[Selector, PageElement],
                      source_text: str = None, target_text: str = None,
                      source_index: int = None, target_index: int = None,
                      sleep: float = 0.5, desc: str = None):
        log(f'[drug_and_drop:{source}->{target}]: {desc}' if desc else None, end=' ... ')
        if isinstance(source, Selector):
            self.wait_until_selector(EC.element_to_be_clickable, source)
        if isinstance(target, Selector):
            self.wait_until_selector(EC.element_to_be_clickable, target)
        source = self.get_page_element(source, element_text=source_text, element_index=source_index)
        target = self.get_page_element(target, element_text=target_text, element_index=target_index)
        self.driver_actions.reset_actions()
        self.driver_actions.drag_and_drop(source, target).perform()
        time.sleep(sleep)
        log(f'done' if desc else None)

    def press_key(self, key, desc: str = None):
        log(f'[press_key:{key}]: {desc}' if desc else None, end=' ... ')
        self.driver_actions.reset_actions()
        self.driver_actions.key_down(key).key_up(key).perform()
        log(f'done' if desc else None)

    def press_Enter(self, desc: str = None):
        log(f'[press_Enter]: {desc}' if desc else None, end=' ... ')
        self.press_key(Keys.ENTER)
        log(f'done' if desc else None)

    def press_Backspace(self, desc: str = None):
        log(f'[press_Backspace]: {desc}' if desc else None, end=' ... ')
        self.press_key(Keys.BACKSPACE)
        log(f'done' if desc else None)

    def press_Tab(self, desc: str = None):
        log(f'[press_Tab]: {desc}' if desc else None, end=' ... ')
        self.press_key(Keys.TAB)
        log(f'done' if desc else None)

    def press_Esc(self, desc: str = None):
        log(f'[press_Esc]: {desc}' if desc else None, end=' ... ')
        self.press_key(Keys.ESCAPE)
        log(f'done' if desc else None)
