from selenium.webdriver.support.expected_conditions import *


class isVisible(object):
    def __init__(self, element: WebElement):
        self.element = element

    def __call__(self, driver):
        return self.element.is_displayed()
