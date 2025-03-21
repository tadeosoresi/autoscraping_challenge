#!/bin/bash

: 'To run: sudo bash up_environment.sh
Important: developed in ubuntu 22.04, must execute in super user mood.'

DEFAULT_ENV_FILE=.env
PATH_SECRETS_ADMIN_FILE=secrets/admin_users.js
PATH_SECRETS_USERS_FILE=secrets/other_users.js

# Corta la ejecucion al primer error.
set -e

setup_ubuntu() {
    echo 'Updating system and installing Python..'
    sudo apt install -y pkg-config default-libmysqlclient-dev python3-dev &&
    sudo apt-get -y install net-tools
}

export_variables() {
    # Loading env vars.
    export $(grep -v '^#' ${DEFAULT_ENV_FILE} | xargs)
    # Seteamos airflow home
    export AIRFLOW_HOME=$(dirname "${PWD}")
    # Configuramos airflow localmente (Executor, folders, etc.)
    export AIRFLOW__CORE__EXECUTOR=LocalExecutor
    export AIRFLOW__CORE__LOAD_EXAMPLES=False
    export AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}
    export AIRFLOW__CORE__DAGS_FOLDER=${AIRFLOW_HOME}/dags
    export AIRFLOW__CORE__BASE_LOG_FOLDER=${AIRFLOW_HOME}/logs
    export AIRFLOW__CORE__PLUGINS_FOLDER=${AIRFLOW_HOME}/plugins
    echo "Variables de ambiente seteadas"
}

launch_scraping_services() {
    echo '\n Launching Docker services... \n'
    docker compose up -d
    docker build -t scraping-image .

}

deploy_executor() {
    if docker ps -a --filter "name=postgres-airflow" --format '{{.Names}}' | grep -q "postgres-airflow"; then
        # Stop and remove the existing container
        echo "Container 'postgres-airflow' already exists. Stopping and removing it."
        docker stop postgres-airflow
        docker rm postgres-airflow
    fi
    docker run -d \
        --name postgres-airflow \
        --restart always \
        --env POSTGRES_USER=${POSTGRES_USER} \
        --env POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
        --env POSTGRES_DB=${POSTGRES_DB} \
        -p 127.0.0.1:5432:5432 \
        --expose 5432 \
        --volume ${DATA_DIR}:/var/lib/postgresql/data \
        --health-cmd="pg_isready -U postgres" \
        --health-interval=5s \
        --health-timeout=5s \
        --health-retries=5 \
        postgres:12.3-alpine
}

launch_local_airflow() {
    echo '\nCreating virtual environment (env)...\n'
    cd .. && python3 -m venv env &&
    echo 'Installing Airflow, setting up Airflow user...' &&
    . env/bin/activate && pip3 install --upgrade pip && \
    pip3 install 'apache-airflow[amazon, mysql]==2.9.0' \
        --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.0/constraints-3.8.txt" \
        --ignore-installed && \
    pip3 install -r airflow_requirements.txt &&
    airflow db init && 
    airflow users create --role Admin \
        --username ${AIRFLOW_USER} --password ${AIRFLOW_PASSWORD} --email tadeosoresi@gmail.com \
        --firstname Data --lastname Engineer &&
    airflow connections add 'MYSQL_CONN_ID' \
                --conn-type 'mysql' \
                --conn-login ${MYSQL_USER} \
                --conn-password ${MYSQL_PASSWORD} \
                --conn-host '127.0.0.1' \
                --conn-port 3306 \
                --conn-schema ${MYSQL_DATABASE} &&
    airflow connections add 'MINIO_CONN_ID' \
                --conn-type aws \
                --conn-extra '{"endpoint_url": "http://localhost:9000"}' \
                --conn-login ${MINIO_ROOT_USER} \
                --conn-password ${MINIO_ROOT_PASSWORD} &&
    airflow webserver -p 32800 --hostname localhost
}

setup_ubuntu
export_variables
launch_scraping_services
deploy_executor
launch_local_airflow
