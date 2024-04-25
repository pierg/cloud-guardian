import json
from botocore.exceptions import ClientError
from cloud_guardian import logger

def get_bucket_policy(s3, bucket_name: str) -> dict:
    try:
        response = s3.get_bucket_policy(Bucket=bucket_name)
        return json.loads(response['Policy'])
    except ClientError as e:
        logger.error(f"Error retrieving policy for bucket {bucket_name}: {e}")
        raise e

def set_bucket_policy(s3, bucket_name: str, policy_document: dict):
    try:
        policy_string = json.dumps(policy_document)
        s3.put_bucket_policy(Bucket=bucket_name, Policy=policy_string)
        logger.info(f"Policy set for bucket {bucket_name}")
    except ClientError as e:
        logger.error(f"Error setting policy for bucket {bucket_name}: {e}")
        raise e

def delete_bucket_policy(s3, bucket_name: str):
    try:
        s3.delete_bucket_policy(Bucket=bucket_name)
        logger.info(f"Policy deleted for bucket {bucket_name}")
    except ClientError as e:
        logger.error(f"Error deleting policy for bucket {bucket_name}: {e}")
        raise e
