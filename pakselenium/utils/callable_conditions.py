from typing import Union, Optional, Callable, List


def is_reached(until: Union[Callable, List[Callable], None]):
    if until is None:
        return True

    if type(until) is list:
        for i in until:
            if not i():
                return False
        return True
    else:
        return until()


def is_empty(empty: Optional[Callable]):
    if empty is None:
        return False
    return empty()


def is_reload(reload: Optional[Callable]):
    if reload is None:
        return False
    return reload()
