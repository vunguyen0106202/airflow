from airflow import DAG
from airflow.operators.python import PythonOperator
from selenium import webdriver
from airflow.operators.python import PythonOperator
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import datetime
from minio import Minio
import logging
import json
import os
from fun.fun_page import Functions  
from selenium.webdriver.chrome.service import Service
from airflow.models import Variable
from selenium.webdriver.chrome.options import Options
#from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
url = Variable.get('URI')
MIN_KEY = Variable.get('USER')
MIN_PASS = Variable.get('PASS')
def run_selenium_job():
    options = Options()
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--incognito")
    options.add_argument("--headless")

    #service = Service(ChromeDriverManager().install())
    service = Service()
    driver = webdriver.Chrome(service=service,options=options)
    #driver=webdriver.Chrome(options=options)
    try:
        access_token = Variable.get('TOKEN')
        functions_instance = Functions()
        link = 'https://www.facebook.com/profile.php?id=100087476232250'
        page_id = functions_instance.get_page_id(driver, link, access_token)
        result = functions_instance.get_all_data(driver, page_id, access_token)
        
        if result is None:
            raise ValueError("Selenium job did not return valid data")
        
        return result
    
    except Exception as e:
        logging.error(f"Error running Selenium job: {str(e)}")
        raise 
    
    finally:
        driver.quit()

def upload_data_to_minio(**kwargs):
    text = kwargs['ti'].xcom_pull(task_ids='run_selenium_task')
    KEY = MIN_KEY
    PASS = MIN_PASS
    client = Minio(url,
        access_key=KEY,
        secret_key=PASS,
        secure=False
    )
    fb_page_id=text.get("fb_page_id")
    bucket_name = "datafbcrawl"
    destination_file = f"page_data/page_data_{fb_page_id}.json"
    
    data_json = json.dumps(text, ensure_ascii=False)
    
    temp_file_path = '/tmp/temporary_data.json'
    with open(temp_file_path, 'w') as temp_file:
        temp_file.write(data_json)
    
    try:
        found = client.bucket_exists(bucket_name)
        if not found:
            client.make_bucket(bucket_name)
            logging.info(f"Created bucket {bucket_name}")
        else:
            logging.info(f"Bucket {bucket_name} already exists")
        
        client.fput_object(bucket_name, destination_file, temp_file_path)
        logging.info(f"Uploaded data as object {destination_file} to bucket {bucket_name}")
        
    except Exception as e:
        logging.error(f"Error uploading data to MinIO: {str(e)}")    

dag = DAG(
    'selenium_minio_',
    description='Run Selenium job and upload h1 text to MinIO',
    schedule_interval=None,  # Thực thi theo cài đặt thời gian
    start_date=datetime.datetime(2024, 6, 20),
    catchup=False,
)

run_selenium_task = PythonOperator(
    task_id='run_selenium_task',
    python_callable=run_selenium_job,
    
    dag=dag,
)

upload_to_minio_task = PythonOperator(
    task_id='upload_to_minio_task',
    python_callable=upload_data_to_minio,
    provide_context=True,  # Cung cấp context để nhận giá trị trả về từ task trước
    dag=dag,
)
run_selenium_task >> upload_to_minio_task
