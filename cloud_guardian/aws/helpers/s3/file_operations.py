from botocore.exceptions import ClientError
from cloud_guardian import logger

def upload_file(s3, bucket_name: str, file_name: str, object_name: str = None):
    if object_name is None:
        object_name = file_name
    try:
        s3.upload_file(file_name, bucket_name, object_name)
        logger.info(f"File {object_name} uploaded to bucket {bucket_name}")
    except ClientError as e:
        logger.error(f"Error uploading file {file_name} to bucket {bucket_name}: {e}")
        raise e

def delete_file(s3, bucket_name: str, object_name: str):
    try:
        s3.delete_object(Bucket=bucket_name, Key=object_name)
        logger.info(f"File {object_name} deleted from bucket {bucket_name}")
    except ClientError as e:
        logger.error(f"Error deleting file {object_name} from bucket {bucket_name}: {e}")
        raise e