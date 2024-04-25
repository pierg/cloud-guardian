import json
from typing import Dict, List, Optional

from botocore.exceptions import ClientError
from loguru import logger


def create_bucket(s3, bucket_name: str, region: Optional[str] = None) -> Optional[str]:
    """
    Create an S3 bucket in a specified region. If no region is specified, the bucket is created in the S3 default region.
    """
    try:
        if region is None:
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
        logger.info(f"Bucket {bucket_name} created")
        return bucket_name
    except ClientError as e:
        logger.error(f"Error creating bucket {bucket_name}: {e}")
        raise e


def get_bucket_policy(s3, bucket_name: str) -> Optional[Dict]:
    """
    Get the policy of an S3 bucket.
    """
    try:
        response = s3.get_bucket_policy(Bucket=bucket_name)
        return json.loads(response["Policy"])
    except ClientError as e:
        logger.error(f"Error retrieving policy for bucket {bucket_name}: {e}")
        return None


def set_bucket_policy(s3, bucket_name: str, policy_document: Dict) -> bool:
    """
    Set the policy of an S3 bucket.
    """
    try:
        policy_string = json.dumps(policy_document)
        s3.put_bucket_policy(Bucket=bucket_name, Policy=policy_string)
        logger.info(f"Policy set for bucket {bucket_name}")
        return True
    except ClientError as e:
        logger.error(f"Error setting policy for bucket {bucket_name}: {e}")
        raise e


def delete_bucket(s3, bucket_name: str) -> bool:
    """
    Delete an S3 bucket.
    """
    try:
        s3.delete_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        logger.error(f"Error deleting bucket {bucket_name}: {e}")
        return False


def list_buckets(s3) -> List[Dict[str, str]]:
    """
    List all S3 buckets in the account.
    """
    try:
        response = s3.list_buckets()
        return [
            {"name": bucket["Name"], "creation_date": bucket["CreationDate"]}
            for bucket in response["Buckets"]
        ]
    except ClientError as e:
        logger.error(f"Error listing buckets: {e}")
        return []


def upload_file(
    s3, bucket_name: str, file_name: str, object_name: Optional[str] = None
) -> bool:
    """
    Upload a file to an S3 bucket.
    """
    if object_name is None:
        object_name = file_name
    try:
        s3.upload_file(file_name, bucket_name, object_name)
        return True
    except ClientError as e:
        logger.error(f"Error uploading file to bucket {bucket_name}: {e}")
        return False


def delete_file(s3, bucket_name: str, object_name: str) -> bool:
    """
    Delete a file from an S3 bucket.
    """
    try:
        s3.delete_object(Bucket=bucket_name, Key=object_name)
        return True
    except ClientError as e:
        logger.error(f"Error deleting file from bucket {bucket_name}: {e}")
        return False


def get_bucket_policy(s3, bucket_name: str) -> Optional[Dict]:
    """
    Get the policy of an S3 bucket.
    """
    try:
        response = s3.get_bucket_policy(Bucket=bucket_name)
        return json.loads(response["Policy"])
    except ClientError as e:
        logger.error(f"Error retrieving policy for bucket {bucket_name}: {e}")
        return None


def set_bucket_policy(s3, bucket_name: str, policy_document: Dict) -> bool:
    """
    Set the policy of an S3 bucket.
    """
    try:
        policy_string = json.dumps(policy_document)
        s3.put_bucket_policy(Bucket=bucket_name, Policy=policy_string)
        return True
    except ClientError as e:
        logger.error(f"Error setting policy for bucket {bucket_name}: {e}")
        return False


def delete_bucket_policy(s3, bucket_name: str) -> bool:
    """
    Delete the policy of an S3 bucket.
    """
    try:
        s3.delete_bucket_policy(Bucket=bucket_name)
        return True
    except ClientError as e:
        logger.error(f"Error deleting policy for bucket {bucket_name}: {e}")
        return False
