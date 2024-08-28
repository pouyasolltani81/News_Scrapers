from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json

# Step 1: Launch the browser and navigate to the site
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://cointelegraph.com/")

# Step 2: Wait for the user to manually solve the CAPTCHA
input("Please solve the CAPTCHA manually and press Enter to continue...")

# Step 3: Save the cookies to a file after CAPTCHA is solved
cookies = driver.get_cookies()
with open("cookies.json", "w") as f:
    json.dump(cookies, f)
    print("Cookies have been saved!")

driver.quit()
