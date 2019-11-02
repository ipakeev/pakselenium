from typing import Union, Callable, Tuple


def _isReachedUntilOr(untilOr: Tuple[Callable, ...]):
    if untilOr is None:
        return True

    for i in untilOr:
        if i():
            return True
    return False


def isReached(until: Union[Callable, Tuple[Callable, ...]], untilOr: Tuple[Callable, ...]):
    if until is None:
        if _isReachedUntilOr(untilOr):
            return True
        return False

    if type(until) is tuple:
        for i in until:
            if not i():
                return False
        if _isReachedUntilOr(untilOr):
            return True
        return False
    else:
        if until():
            if _isReachedUntilOr(untilOr):
                return True
            return False


def isEmpty(empty: Callable):
    if empty is None:
        return False
    return empty()


def isReload(reload: Callable):
    if reload is None:
        return False
    return reload()
