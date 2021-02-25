# pakselenium

## Usage
```python
from pakselenium import Browser, Selector, By, catch, config

# must be 0, 1 or 2
config.debug_verbose = 1

browser = Browser()
browser.init_chrome(chrome_driver_path)
browser.driver.set_window_size(640, 480)

# wait until this selector is on the page
until = Selector(By.CSS_SELECTOR, '.input')

@catch.timeoutException(lambda: browser.refresh())
def go_to_google():
	browser.go('https://google.com', until=until, sleep=5.0, desc='google', timeout=10)
	
go_to_google()
```

until may be:
- Selector
```python
until = Selector(By.CSS_SELECTOR, '.input')
```
- List[Selector]
```python
until = [Selector(By.CSS_SELECTOR, '.input'), Selector(By.CSS_SELECTOR, '.phlogo')]
```
- Callable (returns True if page loaded succesfully)
```python
until = lambda: browser.is_on_page(Selector(By.CSS_SELECTOR, '.input'))

def until():
	return browser.is_on_page(Selector(By.CSS_SELECTOR, '.input')) and browser.is_on_page(Selector(By.CSS_SELECTOR, '.phlogo')):
```
