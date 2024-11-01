from airflow.models import Variable
access_token = Variable.get('TOKEN1')
print(access_token)