from typing import List, Union

from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException

from pakselenium import config
from pakselenium.browser import Browser, Selector


def close_popup(selector: Union[Selector, List[Selector]], desc: str = None,
                before: bool = False, after: bool = False, on_error: bool = False):
    if isinstance(selector, Selector):
        selector = [selector]

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            browser: Browser = self.browser

            if config.debug_verbose >= 2 and desc is not None:
                print(f'[{desc}]: [{self}, {args}, {kwargs}]')

            def do():
                for i in selector:
                    if browser.is_on_page(i):
                        browser.click(i, sleep=2.0)
                        if config.debug_verbose >= 1:
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
                    if config.debug_verbose >= 1:
                        print(f'[{desc}]: caught Exception')
                    if n >= 3:
                        raise
                    if on_error:
                        do()

            if after:
                do()

            return answer

        return wrapper

    return decorator
