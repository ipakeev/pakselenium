import sys
import time
import traceback
from typing import Callable

from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException

from pakselenium.config import debug_verbose, debug_staleElementReferenceException, debug_timeoutException


def staleElementReferenceException(call_on_exception: Callable = None, timer: int = 360, desc: str = None,
                                   print_traceback: bool = False):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if debug_verbose > 1 and desc is not None:
                print(f'[{desc}]: [{self}, {args}, {kwargs}]')

            if debug_staleElementReferenceException:
                return func(self, *args, **kwargs)

            tt = time.time()
            while 1:
                try:
                    return func(self, *args, **kwargs)
                except StaleElementReferenceException as e:
                    # when element is updating
                    if debug_verbose > 0:
                        print(f'[{desc}]: caught StaleElementReferenceException')

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


def timeoutException(call_on_exception: Callable = None, timer: int = 3600, desc: str = None,
                     print_traceback: bool = False):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if debug_verbose > 1 and desc is not None:
                print(f'[{desc}]: [{self}, {args}, {kwargs}]')

            if debug_timeoutException:
                return func(self, *args, **kwargs)

            tt = time.time()
            while 1:
                try:
                    return func(self, *args, **kwargs)
                except TimeoutException as e:
                    # when slow loading elements
                    if debug_verbose > 0:
                        print(f'[{desc}]: caught TimeoutException')

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
