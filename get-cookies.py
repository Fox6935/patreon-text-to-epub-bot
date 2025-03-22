from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

email= "Replace_with_email"
password= "Replace_with_password"

browser = webdriver.Firefox()

browser.get('https://www.patreon.com/login')

browser.find_element(By.NAME, "email").send_keys(email)

time.sleep(1)

submit_button = browser.find_element(By.XPATH, "/html/body/div[1]/main/div/div[1]/div/div/form/div[3]/button")
submit_button.click()

time.sleep(1)

browser.find_element(By.NAME, "current-password").send_keys(password)

time.sleep(1)

submit_button.click()

WebDriverWait(browser, 10).until(
    EC.url_to_be('https://www.patreon.com/home')
)

print("login successful")

cookies = browser.get_cookies()
cookies_json = json.dumps(cookies)

with open('cookies.json', 'w') as file:
    file.write(cookies_json)
time.sleep(2)
browser.quit()