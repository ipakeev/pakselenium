import time
from typing import List, Union, Callable

from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException

from .browser import Browser, Selector


def close_popup(selector: Union[Selector, List[Selector]],
                before: bool = False, after: bool = False, on_error: bool = False):
    if isinstance(selector, Selector):
        selector = [selector]

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            browser: Browser = self.browser

            def do():
                for i in selector:
                    if browser.is_on_page(i):
                        browser.click(i, sleep=2.0)
                        print(f'> closed popup: {i}')

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


def call_if_exception(to_call: Callable, exception=Exception, return_after_call=False):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            browser: Browser = self.browser
            while 1:
                try:
                    return func(self, *args, **kwargs)
                except exception as e:
                    to_call(browser)
                    print(f'>!> call_if_exception (Exception is {repr(e)}')
                    time.sleep(2)
                    if return_after_call:
                        return

        return wrapper

    return decorator
