from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import url_to_be


def isVisible(element: WebElement):
    def wrapper(_):
        return element.is_displayed()

    return wrapper
