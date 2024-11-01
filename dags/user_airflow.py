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

# Lấy các biến từ Airflow Variables
url = Variable.get('URI')
MIN_KEY = Variable.get('USER')
MIN_PASS = Variable.get('PASS')
TOKEN = Variable.get('TOKEN')

def get_data_to_minio():
    KEY = MIN_KEY
    PASS = MIN_PASS
    client = Minio(url,
        access_key=KEY,
        secret_key=PASS,
        secure=False
    )
    bucket_name = "datafbcrawl"
    prefix = "list_url"
    local_dir = '/tmp/page_url'
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    try:
        objects = client.list_objects(bucket_name, prefix=prefix, recursive=True)
        for obj in objects:
            object_name = obj.object_name
            if object_name == 'list_url/user.txt':
                local_file_path = os.path.join(local_dir, os.path.basename(object_name))

                try:
                    client.fget_object(bucket_name, object_name, local_file_path)
                    logging.info(f'Successfully downloaded {object_name} to {local_file_path}')
                    with open(local_file_path, 'r') as file:
                        content = file.read()
                        logging.info(f'Content of {local_file_path}: {content}')
                        links = content.splitlines()
                        return links
                except Exception as e:
                    logging.error(f'Error downloading {object_name} from {bucket_name}: {e}')
    except Exception as e:
        logging.error(f'Error listing objects in {bucket_name}/{prefix}: {e}')

def run_selenium_job(link, **kwargs):
    #link='https://www.facebook.com/mr.gai.tran'
    options = Options()
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--incognito")
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(link)
    page_id=0
    access_token = TOKEN
    functions_instance = User_Functions(includesPosts=True)
    page_id = functions_instance.get_id(driver)  
    result = functions_instance.get_all_data(page_id, access_token)
    
    if result is None:
        raise ValueError("Selenium job did not return valid data")
    
    return result

def upload_data_to_minio( result, **kwargs):
    KEY = MIN_KEY
    PASS = MIN_PASS
    client = Minio(url,
        access_key=KEY,
        secret_key=PASS,
        secure=False
    )
    fb_page_id = result.get("fb_id")
    bucket_name = "datafbcrawl"
    destination_file = f"user_data/user_data_{fb_page_id}.json"
    
    data_json = json.dumps(result, ensure_ascii=False)
    
    temp_file_path = '/tmp/temporary_data.json'
    with open(temp_file_path, 'w') as temp_file:
        temp_file.write(data_json)
    
    try:
        found = client.bucket_exists(bucket_name)
        if not found:
            client.make_bucket(bucket_name)
            logging.info(f"Created bucket {bucket_name}")
        
        try:
            client.fget_object(bucket_name, destination_file, "/tmp/check_temp_file.json")
            index = 1
            while True:
                destination_file = f"user_data/user_data_{fb_page_id}_{index}.json"
                try:
                    client.fget_object(bucket_name, destination_file, "/tmp/check_temp_file.json")
                except:
                    break
                index += 1
        except:
            destination_file = destination_file

        client.fput_object(bucket_name, destination_file, temp_file_path)
        logging.info(f"Uploaded data as object {destination_file} to bucket {bucket_name}")
        
    except Exception as e:
        logging.error(f"Error uploading data to MinIO: {str(e)}")
    finally:
        if os.path.isfile(temp_file_path):
            os.remove(temp_file_path)

def process_link(**kwargs):
    ti = kwargs['ti']
    links = ti.xcom_pull(task_ids='get_urls_task')
    
    for link in links:
        result = run_selenium_job(link)
        upload_data_to_minio(result)
# Định nghĩa DAG
dag = DAG(
    'USER1',
    description='Run Selenium job and upload data to MinIO',
    schedule_interval=None, # '@daily'  # Thực thi theo cài đặt thời gian
    start_date=datetime(2024, 6, 20),
    catchup=False,
)

# Task lấy dữ liệu từ MinIO
get_urls_task1 = PythonOperator(
    task_id='get_urls_task',
    python_callable=get_data_to_minio,
    provide_context=True,
    dag=dag,
)

task1_result = get_urls_task1.execute(context={})
task2 = PythonOperator(
    task_id=f'process_link',
    python_callable=process_link,
    #op_args=[link],
    provide_context=True,
    dag=dag,
)
get_urls_task1 >> task2
