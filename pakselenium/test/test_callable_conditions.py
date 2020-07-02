from pakselenium.utils import callable_conditions as CC


def true():
    return True


def false():
    return False


def test_isReached():
    assert CC.is_reached(None) is True
    assert CC.is_reached(true) is True
    assert CC.is_reached(false) is False
    assert CC.is_reached([true, false]) is False
    assert CC.is_reached([false, false]) is False
    assert CC.is_reached([true, true]) is True


def test_isEmpty():
    assert CC.is_empty(None) is False
    assert CC.is_empty(true) is True
    assert CC.is_empty(false) is False


def test_isReload():
    assert CC.is_reload(None) is False
    assert CC.is_reload(true) is True
    assert CC.is_reload(false) is False
