FROM apache/airflow:2.9.2
ENV PYTHONPATH="/opt/airflow/code/:/opt/airflow/include/:${PYTHONPATH}"
# Cài đặt các gói hệ thống cần thiết cho selenium
USER root
RUN apt-get update && apt-get install -y \
    python3-selenium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*
USER airflow

COPY requirements.txt /requirements.txt

RUN pip install -r  /requirements.txt
RUN pip install --upgrade pip
RUN pip install apache-airflow[postgres,mysql,s3]
RUN pip install minio
# Install other dependencies
RUN pip install selenium requests
RUN pip install numpy
RUN pip install --no-cache-dir \
    webdriver_manager 
RUN pip install webdriver_manager
RUN pip install webdriver_manager==4.0.1

COPY dags /opt/airflow/dags
COPY plugins /opt/airflow/plugins

# Set Airflow home
ENV AIRFLOW_HOME=/opt/airflow

