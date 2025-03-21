#!/bin/bash

: 'To run: sudo bash up_environment.sh
Important: developed in ubuntu 22.04, must execute in super user mood.'

DEFAULT_ENV_FILE=.env
PATH_SECRETS_ADMIN_FILE=secrets/admin_users.js
PATH_SECRETS_USERS_FILE=secrets/other_users.js

# Corta la ejecucion al primer error.
set -e

run_scheduler() {
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
    cd .. && . env/bin/activate && airflow scheduler
}

run_scheduler