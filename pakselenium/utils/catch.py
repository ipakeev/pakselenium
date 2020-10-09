import sys
import time
import traceback
from typing import Callable

from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException

from pakselenium import config


def staleElementReferenceException(to_call: Callable = None,
                                   desc: str = None, print_traceback: bool = False,
                                   return_on_exception: bool = False, sleep: int = 0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if config.debug_verbose >= 2 and desc is not None:
                print(f'[{desc}]: [{args}, {kwargs}]')

            if config.debug_all or config.debug_staleElementReferenceException:
                return func(*args, **kwargs)

            while 1:
                try:
                    return func(*args, **kwargs)
                except StaleElementReferenceException as e:
                    # when element is updating
                    if config.debug_verbose >= 1:
                        print(f'[{desc}]: caught StaleElementReferenceException')

                    if print_traceback:
                        exc_info = sys.exc_info()
                        traceback.print_exception(*exc_info)

                    if callable(to_call):
                        if to_call():
                            return e

                    if return_on_exception:
                        return e
                except Exception as e:
                    if print_traceback:
                        exc_info = sys.exc_info()
                        traceback.print_exception(*exc_info)
                    raise e

                time.sleep(sleep)

        return wrapper

    return decorator


def timeoutException(to_call: Callable = None,
                     desc: str = None, print_traceback: bool = False,
                     return_on_exception: bool = False, sleep: int = 0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if config.debug_verbose >= 2 and desc is not None:
                print(f'[{desc}]: [{args}, {kwargs}]')

            if config.debug_all or config.debug_timeoutException:
                return func(*args, **kwargs)

            while 1:
                try:
                    return func(*args, **kwargs)
                except TimeoutException as e:
                    # when slow loading elements
                    if config.debug_verbose >= 1:
                        print(f'[{desc}]: caught TimeoutException')

                    if print_traceback:
                        exc_info = sys.exc_info()
                        traceback.print_exception(*exc_info)

                    if callable(to_call):
                        if to_call():
                            return e

                    if return_on_exception:
                        return e
                except Exception as e:
                    if print_traceback:
                        exc_info = sys.exc_info()
                        traceback.print_exception(*exc_info)
                    raise e

                time.sleep(sleep)

        return wrapper

    return decorator


def call_if_exception(to_call: Callable, exception=Exception,
                      desc: str = None, print_traceback: bool = False,
                      return_on_exception: bool = False, sleep: int = 0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if config.debug_verbose >= 2 and desc is not None:
                print(f'[{desc}]: [{args}, {kwargs}]')

            if config.debug_all:
                return func(*args, **kwargs)

            while 1:
                try:
                    return func(*args, **kwargs)
                except exception as e:
                    if config.debug_verbose >= 1:
                        print(f'[{desc}]: caught {repr(e)}')

                    if print_traceback:
                        exc_info = sys.exc_info()
                        traceback.print_exception(*exc_info)

                    if to_call(*args, **kwargs):
                        return e

                    if return_on_exception:
                        return e

                    time.sleep(sleep)

        return wrapper

    return decorator
