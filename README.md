<!-- README --->

# Challenge AutoScraping

## Descripción
ETL en el cual se setean distintas tablas en MySQL y se scrapean data de autobuses
insertando dicho scraping a lo largo de las tablas.
Tambien tiene un apartado de logs que se suben al S3 (Minio) en caso de que falle
el scraping.
Las tecnologias se despliegan en Docker, y el ETL se orquesta con airflow.

## Fuentes de Datos
Scraping de pagina de autobuses

## Herramientas de Desarrollo
- Python 🐍
- Docker 🐋
- Airflow 🚀
- MySQL ⭐


### DEPLOY PROYECTO (UBUNTU 22.04) ###
1. Ingresar a la carpeta deploy
2. 
   ```
   sudo sh deploy_etl.sh
   ```
   Este comando levantara los contenedores de MySQL (Database), Minio (logs) e instala Airflow localmente
   con PostgreSQL (LocalExecutor).
3. En otra consola ejecutar (carpeta deploy):
   ```
   sudo sh deploy_scheduler.sh
   ```
   Este comando levantara el Airflow scheduler

### EJECUCIÓN DEL ETL (Via AIRFLOW) ###
1. Ingresar a http://localhost:32800/ y acceder con las credenciales de airflow (estan en el .env)
2. Despausar y ejecutar etl_dag_v1 (corre diariamente)



