from typing import Union, Optional, Callable, Tuple


def isReached(until: Union[Callable, Tuple[Callable, ...], None]):
    if until is None:
        return True

    if type(until) is tuple:
        for i in until:
            if not i():
                return False
        return True
    else:
        return until()


def isEmpty(empty: Optional[Callable]):
    if empty is None:
        return False
    return empty()


def isReload(reload: Optional[Callable]):
    if reload is None:
        return False
    return reload()
