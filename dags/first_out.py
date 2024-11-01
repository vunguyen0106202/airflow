from airflow import DAG
from airflow.operators.python import PythonOperator
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from airflow.models import Variable
from datetime import datetime
from minio import Minio
import logging
import json
import os
from fun.fun_user import User_Functions
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
# Lấy các biến từ Airflow Variables
url = Variable.get('URI')
MIN_KEY = Variable.get('USER')
MIN_PASS = Variable.get('PASS')
TOKEN = Variable.get('TOKEN')

def run_selenium_job():
    link='https://www.facebook.com/profile.php?id=100037069742016'
    options = Options()
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--incognito")
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    # driver.get('https://www.facebook.com/')
    # username_box = driver.find_element(By.ID, 'email')
    # password_box = driver.find_element(By.ID, 'pass')
    # submit_button = driver.find_element(By.XPATH, "//button[contains(@type, 'submit')]")
    # USERNAME = 'saokoyeu2002@gmail.com'
    # PASSWORD = 'vu01062002'
    # username_box.send_keys(USERNAME)
    # password_box.send_keys(PASSWORD)
    # driver.execute_script("arguments[0].click();", submit_button)
    driver.get(link)
    page_id=0
    access_token = TOKEN
    functions_instance = User_Functions(includesPosts=True)
    page_id = functions_instance.get_id(driver)  
    result = functions_instance.get_all_data(page_id, access_token)
    
    if result is None:
        raise ValueError("Selenium job did not return valid data")
    
    return result

# Định nghĩa DAG
dag = DAG(
    'test',
    description='Run Selenium job and upload data to MinIO',
    schedule_interval=None, # '@daily'  # Thực thi theo cài đặt thời gian
    start_date=datetime(2024, 6, 20),
    catchup=False,
)

# Task lấy dữ liệu từ MinIO
get_urls_task1 = PythonOperator(
    task_id='get_urls_task',
    python_callable=run_selenium_job,
    provide_context=True,
    dag=dag,
)
