'''
=======================================================================================================

Nama : Evan Juanto
Batch : BSD-006
Program ini dibuat untuk mengambil data dari Postgres, clean data, dan insert data ke elastic search 
menggunakan airflow

=======================================================================================================
'''
# import libraries
import datetime as dt
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import pandas as pd
import psycopg2 as db
from elasticsearch import Elasticsearch
# fungsi untuk mengambil data dari postgres sql
def queryPostgresql():
    conn_string="dbname='airflow' host='postgres' user='airflow' password='airflow'"
    conn=db.connect(conn_string)
    df=pd.read_sql("select * from table_m3",conn)
    df.to_csv('/opt/airflow/dags/P2M3_Evan_Juanto_data_raw.csv',index=False)
    print("-------Data Saved------")
# fungsi untuk clean data 
def clean_data():
    df = pd.read_csv('/opt/airflow/dags/P2M3_Evan_Juanto_data_raw.csv')
    # ubah nama
    df = df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"))
    # missing values
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns
    for col in categorical_columns:
        df[col] = df[col].fillna(df[col].mode())
    # missing values
    numerical_columns = df.select_dtypes(include=['number']).columns
    for col in numerical_columns:
        df[col] = df[col].fillna(df[col].median())
    # duplicate rows
    df = df.drop_duplicates() 
    df.to_csv('/opt/airflow/dags/P2M3_Evan_Juanto_data_cleaned.csv',index=False)
# fungsi untuk input ke elasticsearch
def insertElasticsearch():
    es = Elasticsearch() 
    df=pd.read_csv('/opt/airflow/dags/P2M3_Evan_Juanto_data_cleaned.csv')
    for i,r in df.iterrows():
        doc=r.to_json()
        res=es.index(index="frompostgresql",doc_type="doc",body=doc)
        print(res)	


default_args = {
    'owner': 'juanto',
    'start_date': dt.datetime(2024, 7, 7),
    'retries': 1,
    'retry_delay': dt.timedelta(minutes=5),
}


with DAG('MyDBdag',
         default_args=default_args,
         schedule_interval='30 6 * * *',      # '0 * * * *',
         ) as dag:

    getData = PythonOperator(task_id='QueryPostgreSQL',
                                 python_callable=queryPostgresql)
    cleandata = PythonOperator(task_id = 'DataCleaning',
                                 python_callable=clean_data)
    insertData = PythonOperator(task_id='InsertDataElasticsearch',
                                 python_callable=insertElasticsearch)



getData >> cleandata >> insertData