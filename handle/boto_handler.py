import boto3
from botocore.client import Config

class BotoHandler():
    """
    Clase para manejar Boto3 y la interacción con Minio (S3)
    """
    def __init__(self, endpoint_url:str, aws_key:str, aws_secret:str):
        self.__miniO_client = boto3.client(
                    's3',
                    endpoint_url=endpoint_url,
                    aws_access_key_id=aws_key,
                    aws_secret_access_key=aws_secret,
                    config=Config(signature_version='s3v4'),
                    region_name='us-east-1'
                )
        print("Connected to AWS Object Storage")
        
    def put_log(self, bucket:str, key:str, body:str) -> None:
        """
        Realiza el upload del log (traceback str) al S3
        """
        self.__miniO_client.put_object(Bucket=bucket, Key=key,
                                Body=body, ContentType='text/plain')
    
    def close(self):
        """
        Cierra conexión al S3
        """
        self.__miniO_client.close()
        