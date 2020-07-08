import time
from typing import List, Union
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from .browser import Browser, Selector


def close_popup(selector: Union[Selector, List[Selector]]):
    if isinstance(selector, Selector):
        selector = [selector]

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            browser: Browser = self.browser
            n = 0
            while 1:
                n += 1
                try:
                    return func(self, *args, **kwargs)
                except (NoSuchElementException, ElementClickInterceptedException):
                    if n >= 3:
                        raise
                    for i in selector:
                        if browser.is_on_page(i):
                            browser.click(i)
                            print(f'> closed popup: {i}')

        return wrapper

    return decorator


def wait_error_page(selector: Union[Selector, List[Selector]]):
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
