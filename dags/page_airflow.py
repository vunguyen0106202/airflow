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
from airflow.models import Variable

url = Variable.get('URI')
MIN_KEY = Variable.get('USER')
MIN_PASS = Variable.get('PASS')


def get_data_to_minio():
    KEY = MIN_KEY
    PASS = MIN_PASS
    client = Minio(url,
        access_key=KEY,
        secret_key=PASS,
        secure=False
    )
    bucket_name = "datafbcrawl"
    prefix = "user_data"
    prefix="list_url"
    local_dir=  '/tmp/page_url'
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    try:
        objects = client.list_objects(bucket_name, prefix=prefix, recursive=True)
        for obj in objects:
            object_name = obj.object_name
            if(object_name=='list_url/page.txt'):
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

def run_selenium_job(link):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless') 
    driver = webdriver.Chrome(options=chrome_options)
    #link='https://www.facebook.com/RFAVietnam'
    try:
        access_token = Variable.get('TOKEN')
        
        functions_instance = Functions()  
        page_id = functions_instance.get_page_id(driver,link,access_token)
        print(page_id)
        result = functions_instance.get_all_data(driver, page_id, access_token)
        print(result)
        if result is None:
            raise ValueError("Selenium job did not return valid data")
        
        return result
    finally:
        driver.quit()

def upload_data_to_minio(link, result):
    #text = kwargs['ti'].xcom_pull(task_ids='run_selenium_task')
    KEY = MIN_KEY
    PASS = MIN_PASS
    client = Minio(url,
        access_key=KEY,
        secret_key=PASS,
        secure=False
    )
    fb_page_id=result.get("fb_page_id")
    bucket_name = "datafbcrawl"
    destination_file = f"page_data/page_data_{fb_page_id}.json"
    
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
            # If we're here, the object exists, we need to find a new filename
            index = 1
            while True:
                destination_file = f"page_data/page_data_{fb_page_id}_{index}.json"
                try:
                    client.fget_object(bucket_name, destination_file, "/tmp/check_temp_file.json")
                except :
                    break
                index += 1
        except :
            destination_file = destination_file

        
        client.fput_object(bucket_name, destination_file, temp_file_path)
        logging.info(f"Uploaded data as object {destination_file} to bucket {bucket_name}")
        
    except Exception as e:
        logging.error(f"Error uploading data to MinIO: {str(e)}")
    finally:
        if os.path.isfile(temp_file_path):
            os.remove(temp_file_path)    

def process_link(link):
    result = run_selenium_job(link)
    upload_data_to_minio(link, result)

dag = DAG(
    'PAGE',
    description='Run Selenium job and upload h1 text to MinIO',
    schedule_interval=None, #'@daily'  # Thực thi theo cài đặt thời gian
    start_date=datetime.datetime(2024, 6, 20),
    catchup=False,
)

get_urls_task = PythonOperator(
    task_id='get_urls_task',
    python_callable=get_data_to_minio,
    dag=dag,
)

# Lấy danh sách URL từ task 'get_urls_task'
urls = get_urls_task.execute(context={})

# Tạo task để xử lý từng URL

for i, link in enumerate(urls):
    task = PythonOperator(
        task_id=f'process_link_{i}',
        python_callable=process_link,
        op_args=[link],
        dag=dag,
    )
    get_urls_task >> task




# run_selenium_task = PythonOperator(
#     task_id='run_selenium_task',
#     python_callable=run_selenium_job,
    
#     dag=dag,
# )

# upload_to_minio_task = PythonOperator(
#     task_id='upload_to_minio_task',
#     python_callable=upload_data_to_minio,
#     provide_context=True,  # Cung cấp context để nhận giá trị trả về từ task trước
#     dag=dag,
# )
# run_selenium_task >> upload_to_minio_task
