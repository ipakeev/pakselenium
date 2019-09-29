from typing import Union, Callable, Tuple


def isReached(until: Union[Callable, Tuple[Callable]]):
    if until is None:
        return True

    if type(until) is tuple:
        for i in until:
            if not i():
                return False
        return True
    else:
        if until():
            return True


def isEmpty(empty: Callable):
    if empty is None:
        return False
    return empty()


def isReload(reload: Callable):
    if reload is None:
        return False
    return reload()
