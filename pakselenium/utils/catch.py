import time
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException

from ..config import GLOBAL


def staleElementReferenceException(func):
    def wrapper(self, *args, **kwargs):
        if GLOBAL.debug:
            return func(self, *args, **kwargs)

        while 1:
            try:
                return func(self, *args, **kwargs)
            except StaleElementReferenceException:
                # when element is updating
                # exc_info = sys.exc_info()
                # traceback.print_exception(*exc_info)
                pass
            except Exception as e:
                print('pakselenium staleElementReferenceException:', func, args, kwargs)
                raise e
            time.sleep(1)

    return wrapper


def timeoutException(func):
    def wrapper(self, *args, **kwargs):
        if GLOBAL.debug:
            return func(self, *args, **kwargs)

        while 1:
            try:
                return func(self, *args, **kwargs)
            except TimeoutException:
                # when slow loading elements
                pass
            except Exception as e:
                print('pakselenium timeoutException:', func, args, kwargs)
                raise e
            time.sleep(5)

    return wrapper
