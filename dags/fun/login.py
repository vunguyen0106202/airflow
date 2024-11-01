from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup 
from dotenv import load_dotenv

import pickle
import requests
import json
import time
import csv
import random
import os

ads_manager_url = 'https://adsmanager.facebook.com/adsmanager/manage/ad_account_settings/ad_account_setup?act=264708371188743'
class Login:
    def __init__(self, driver) -> None:
        self.driver = driver
        
    def account_setup(self):
        rand_num = random.randint(1,2)
        
        load_dotenv('configs/.env')

        USERNAME = os.getenv(f'USERNAME{rand_num}')
        PASSWORD = os.getenv(f'PASSWORD{rand_num}')
        
        return USERNAME, PASSWORD

    def begin(self):
        self.driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(2, 5))

        username_box = self.driver.find_element(By.ID, 'email')
        password_box = self.driver.find_element(By.ID, 'pass')
        submit_button = self.driver.find_element(By.XPATH, "//button[contains(@type, 'submit')]")

        load_dotenv('configs/.env')

        USERNAME, PASSWORD = self.account_setup()

        username_box.send_keys(USERNAME)

        time.sleep(2)

        password_box.send_keys(PASSWORD)

        time.sleep(2)

        self.driver.execute_script("arguments[0].click();", submit_button)
        
        

    def insta_login(self):
        self.driver.get("https://instagram.com/")
        time.sleep(random.uniform(3, 5))

    def initialize_browser(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-gpu')

        driver = webdriver.Chrome(options=options)

        driver.get("https://www.facebook.com/")
        time.sleep(random.uniform(2, 5))
        return driver
    
    def get_access_token(self):
        self.driver.get(ads_manager_url)

        time.sleep(random.uniform(8,10))

        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        time.sleep(random.uniform(5, 7))

        text = soup.prettify()
        index = text.find('accessToken')

        # with open('test.txt', 'w', encoding='utf-8') as file:
        #     file.write(text)

        access_token = text[index+13:].split('"')[0]

        for i in range(len(access_token)):
            if access_token[i] == '"':
                return access_token[0:i]
            
    def get_access_token_friends(self):
        self.driver.get("")