import time
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException

from ..config import GLOBAL


def staleElementReferenceException(func):
    def wrapper(self, *args, **kwargs):
        if GLOBAL.debug:
            return func(self, *args, **kwargs)

        tt = time.time()
        while 1:
            try:
                return func(self, *args, **kwargs)
            except StaleElementReferenceException:
                # when element is updating
                # exc_info = sys.exc_info()
                # traceback.print_exception(*exc_info)
                if time.time() - tt > 360:
                    print('>!> raising StaleElementReferenceException')
                    raise StaleElementReferenceException
            except Exception as e:
                print('pakselenium staleElementReferenceException:', func, args, kwargs)
                raise e
            time.sleep(1)

    return wrapper


def timeoutException(func):
    def wrapper(self, *args, **kwargs):
        if GLOBAL.debug:
            return func(self, *args, **kwargs)

        tt = time.time()
        while 1:
            try:
                return func(self, *args, **kwargs)
            except TimeoutException:
                # when slow loading elements
                if time.time() - tt > 3600:
                    print('>!> raising TimeoutException')
                    raise TimeoutException
            except Exception as e:
                print('pakselenium timeoutException:', func, args, kwargs)
                raise e
            time.sleep(5)

    return wrapper
