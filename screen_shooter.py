from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
service = Service('/path/to/chromedriver')  # chromedriver joylashgan to‘liq yo‘l

options = Options()
options.add_argument("--headless")
options.add_argument("--start-maximized")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(service=service, options=options)

url = 'https://detail.1688.com/offer/661672664326.html?spm=a26352.b28411319.offerlist.8.54f51e62U62vNR'
url_list = [url, url]

for i, url in enumerate(url_list):
    driver.get(url)

    # To‘liq sahifani scroll qilish
    S = lambda X: driver.execute_script('return document.body.parentNode.scroll' + X)
    driver.set_window_size(S('Width'), S('Height'))  # sahifa o‘lchamini to‘liq qildi

    # Skrinshot olish
    driver.save_screenshot(f"screenshot{i}.png")

    driver.quit()
