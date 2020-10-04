import time
from typing import List, Union, Callable

from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException

from pakselenium.browser import Browser, Selector
from pakselenium.config import debug_verbose


def close_popup(selector: Union[Selector, List[Selector]], desc: str = None,
                before: bool = False, after: bool = False, on_error: bool = False):
    if isinstance(selector, Selector):
        selector = [selector]

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            browser: Browser = self.browser

            if debug_verbose > 1 and desc is not None:
                print(f'[{desc}]: [{self}, {args}, {kwargs}]')

            def do():
                for i in selector:
                    if browser.is_on_page(i):
                        browser.click(i, sleep=2.0)
                        if debug_verbose > 0:
                            print(f'[{desc}]: closed popup: {i.desc}')

            if before:
                do()

            n = 0
            while 1:
                n += 1
                try:
                    answer = func(self, *args, **kwargs)
                    break
                except (NoSuchElementException, ElementClickInterceptedException):
                    if n >= 3:
                        raise
                    if on_error:
                        do()

            if after:
                do()

            return answer

        return wrapper

    return decorator


def call_if_exception(to_call: Callable, desc: str = None, exception=Exception, return_after_call=False):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            browser: Browser = self.browser
            if debug_verbose > 1 and desc is not None:
                print(f'[{desc}]: [{self}, {args}, {kwargs}]')

            while 1:
                try:
                    return func(self, *args, **kwargs)
                except exception as e:
                    if debug_verbose > 0:
                        print(f'[{desc}]: caught {repr(e)}')
                    to_call(browser)
                    time.sleep(2)
                    if return_after_call:
                        return

        return wrapper

    return decorator
