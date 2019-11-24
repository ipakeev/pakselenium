from pakselenium.utils import callable_conditions as CC


def true():
    return True


def false():
    return False


def test_isReached():
    assert CC.isReached(None) == True
    assert CC.isReached(true) == True
    assert CC.isReached(false) == False
    assert CC.isReached((true, false)) == False
    assert CC.isReached((false, false)) == False
    assert CC.isReached((true, true)) == True


def test_isEmpty():
    assert CC.isEmpty(None) == False
    assert CC.isEmpty(true) == True
    assert CC.isEmpty(false) == False


def test_isReload():
    assert CC.isReload(None) == False
    assert CC.isReload(true) == True
    assert CC.isReload(false) == False
