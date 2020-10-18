# pakselenium

## Usage
```python
from pakselenium import Browser, Selector, By, catch, config

config.debug_verbose = 1

browser = Browser()
browser.init_chrome(chrome_driver_path)
browser.driver.set_window_size(640, 480)

@catch.timeoutException(lambda: browser.refresh())
def go_to_google():
	browser.go('https://google.com', until=Selector(By.CSS_SELECTOR, '.input'), sleep=5.0, desc='google', timeout=10)
	
go_to_google()
```
