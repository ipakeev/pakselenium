import time
from typing import List, Union

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


def wait_on_error_page(selector: Union[Selector, List[Selector]]):
    if isinstance(selector, Selector):
        selector = [selector]

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            browser: Browser = self.browser
            while 1:
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    if any([browser.is_on_page(i) for i in selector]):
                        print(f'>!> Error page (Exception is {e}')
                        time.sleep(60)
                        browser.refresh()
                        continue
                    else:
                        raise e

        return wrapper

    return decorator
