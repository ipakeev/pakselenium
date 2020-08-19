import sys
import time
import traceback
from typing import Callable

from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException

debug_staleElementReferenceException: bool = False
debug_timeoutException: bool = False


def staleElementReferenceException(call_on_exception: Callable = None, timer: int = 360, print_traceback: bool = True):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if debug_staleElementReferenceException:
                return func(self, *args, **kwargs)

            tt = time.time()
            while 1:
                try:
                    return func(self, *args, **kwargs)
                except StaleElementReferenceException as e:
                    # when element is updating
                    if print_traceback:
                        exc_info = sys.exc_info()
                        traceback.print_exception(*exc_info)

                    if callable(call_on_exception):
                        call_on_exception()

                    if time.time() - tt > timer:
                        print('>!> raising StaleElementReferenceException:', func, args, kwargs)
                        raise e
                except Exception as e:
                    if print_traceback:
                        exc_info = sys.exc_info()
                        traceback.print_exception(*exc_info)
                    raise e
                time.sleep(1)

        return wrapper

    return decorator


def timeoutException(call_on_exception: Callable = None, timer: int = 3600, print_traceback: bool = True):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if debug_timeoutException:
                return func(self, *args, **kwargs)

            tt = time.time()
            while 1:
                try:
                    return func(self, *args, **kwargs)
                except TimeoutException as e:
                    # when slow loading elements
                    if print_traceback:
                        exc_info = sys.exc_info()
                        traceback.print_exception(*exc_info)

                    if callable(call_on_exception):
                        call_on_exception()

                    if time.time() - tt > timer:
                        print('>!> raising TimeoutException:', func, args, kwargs)
                        raise e
                except Exception as e:
                    if print_traceback:
                        exc_info = sys.exc_info()
                        traceback.print_exception(*exc_info)
                    raise e
                print('>!> refresh on timeoutException')
                self.refresh()
                time.sleep(5)

        return wrapper

    return decorator
