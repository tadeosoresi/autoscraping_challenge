import os
import sys
import time
import json
import pendulum
from datetime import datetime, timedelta
from airflow import DAG
from docker.types import Mount
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.docker_operator import DockerOperator
from airflow.providers.common.sql.sensors.sql import SqlSensor
from airflow.providers.mysql.operators.mysql import MySqlOperator
from airflow.providers.amazon.aws.operators.s3 import S3CreateBucketOperator

date_of_execution = time.strftime("%Y-%m-%d")
print(f'Date of execution: {date_of_execution}')

def check_bucket(bucket_name:str, conn_id:str) -> None:
    """
    Función para validar el Bucket en AWS (Minio) via S3Hook.
    Args:
        bucket_name:str
        aws_conn_id:str
    Retuns:
        None
    """
    s3_hook = S3Hook(conn_id)
    bucket_exists = s3_hook.check_for_bucket(bucket_name)
    assert bucket_exists, f'Bucket {bucket_name} not exists! creating...'
    
default_args = {
                'owner': 'TadeoSoresi',
                'retries': 5,
                'retry_delay': timedelta(minutes=1),
                'execution_timeout': timedelta(hours=24)
                }
with DAG(
        dag_id='etl_dag_v1',
        start_date=pendulum.yesterday(),
        catchup=False,
        schedule_interval='@daily',
        template_searchpath=[os.path.abspath('./database/queries')]
    ) as dag:
        # Group to setup MySQL and tables
        with TaskGroup(group_id='database_setup_group') as database_setup:
            check_buses_table = SqlSensor(
                task_id='check_buses_table',
                conn_id='MYSQL_CONN_ID',
                sql="""SELECT 1 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_SCHEMA = 'scraping_data' 
                        AND TABLE_NAME = 'buses';""",
                timeout=30,
                poke_interval=5
            )
            
            create_buses_table = MySqlOperator(
                task_id='create_buses',
                mysql_conn_id='MYSQL_CONN_ID',
                sql="buses.sql",
                trigger_rule=TriggerRule.ALL_FAILED
            )
            
            check_buses_overview_table = SqlSensor(
                task_id='check_buses_overview_table',
                conn_id='MYSQL_CONN_ID',
                sql="""SELECT 1 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_SCHEMA = 'scraping_data' 
                        AND TABLE_NAME = 'buses_overview';""",
                timeout=30,
                poke_interval=5
            )
            create_buses_overview_table = MySqlOperator(
                task_id='create_buses_overview',
                mysql_conn_id='MYSQL_CONN_ID',
                sql="buses_overview.sql",
                trigger_rule=TriggerRule.ALL_FAILED
            )
            
            check_buses_images_table = SqlSensor(
                task_id='check_buses_images_table',
                conn_id='MYSQL_CONN_ID',
                sql="""SELECT 1 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_SCHEMA = 'scraping_data' 
                        AND TABLE_NAME = 'buses_images';""",
                timeout=30,
                poke_interval=5
            )
            
            create_buses_images_table = MySqlOperator(
                task_id='create_buses_images',
                mysql_conn_id='MYSQL_CONN_ID',
                sql="buses_images.sql",
                trigger_rule=TriggerRule.ALL_FAILED
            )
            
            final_task = DummyOperator(
                task_id='dummy_operator', 
                trigger_rule=TriggerRule.NONE_FAILED,
                dag=dag
            )
        [check_buses_table >> create_buses_table, 
        check_buses_overview_table >> create_buses_overview_table,
        check_buses_images_table >> create_buses_images_table] >> final_task
        
        with TaskGroup(group_id='object_storage_group') as object_storage_setup: 
            check_bucket_task = PythonOperator(
                task_id='check_s3_bucket',
                python_callable=check_bucket,
                op_kwargs={'bucket_name': 'scraping-data', 
                            'conn_id': 'MINIO_CONN_ID'},
                dag=dag
            )
            create_bucket_task = S3CreateBucketOperator(
                task_id='create_s3_bucket',
                aws_conn_id='MINIO_CONN_ID',
                bucket_name='scraping-data',
                trigger_rule=TriggerRule.ALL_FAILED,
                dag=dag
            )
            
            check_bucket_task >> create_bucket_task
            
        with TaskGroup(group_id='scraping_group') as scraping_group:    
            project_dir = os.path.dirname(os.path.dirname(__file__))
            commands = ["sh", "-c", f'pip install -r scraping_requirements.txt && python3 extract/ross_buses.py']            
            # AWS Lambda 
            # Realizamos deploy de contenedor para el scraping y posteriormente lo destruimos
            launch_scraping_container = DockerOperator(
                    task_id='launch_scraping_container',
                    execution_timeout=timedelta(hours=4),
                    image='scraping-image',
                    container_name='scraping-container',
                    working_dir="/home/scraping-etl/",
                    network_mode="etl-network",
                    cpus = 0.75,
                    private_environment={
                        "MYSQL_DATABASE": os.environ.get("MYSQL_DATABASE"), # Lo ideal es usar airflow variables           
                        "MYSQL_USER": os.environ.get("MYSQL_USER"),                      
                        "MYSQL_PASSWORD": os.environ.get("MYSQL_PASSWORD"),
                        "MINIO_ROOT_USER": os.environ.get("MINIO_ROOT_USER"),
                        "MINIO_ROOT_PASSWORD": os.environ.get("MINIO_ROOT_PASSWORD")
                    },
                    mounts=[
                        Mount(source=os.path.abspath(os.path.join(project_dir, 'extract')), 
                              target='/home/scraping-etl/extract/', 
                              type='bind'),
                        Mount(source=os.path.abspath(os.path.join(project_dir, 'handle')), 
                              target='/home/scraping-etl/handle/', 
                              type='bind'),
                        Mount(source=os.path.abspath(os.path.join(project_dir, 'scraping_requirements.txt')), 
                              target='/home/scraping-etl/scraping_requirements.txt', 
                              type='bind'),
                    ],
                    shm_size=2147483648,
                    tty=True,
                    privileged=True,
                    auto_remove="force",
                    command=commands,
                    trigger_rule=TriggerRule.ALL_DONE,
            )
            
            launch_scraping_container

        database_setup >> object_storage_setup >> scraping_group
