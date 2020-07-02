from selenium.webdriver.support.expected_conditions import *


class is_visible(object):
    def __init__(self, element: WebElement):
        self.element = element

    def __call__(self, driver):
        return self.element.is_displayed()


class is_enabled(object):
    def __init__(self, element: WebElement):
        self.element = element

    def __call__(self, driver):
        return self.element.is_enabled()


class is_selected(object):
    def __init__(self, element: WebElement):
        self.element = element

    def __call__(self, driver):
        return self.element.is_selected()
