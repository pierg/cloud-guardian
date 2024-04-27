from botocore.exceptions import ClientError
from cloud_guardian import logger
import boto3

def create_bucket(s3, bucket_name: str, region: str = None) -> str:
    try:
        if region:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
        else:
            s3.create_bucket(Bucket=bucket_name)
        logger.info(f"Bucket {bucket_name} created successfully.")
        return bucket_name
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'BucketAlreadyExists':
            logger.warning(f"Bucket {bucket_name} already exists and is owned by another user.")
            return bucket_name
        else:
            logger.error(f"Error creating bucket {bucket_name}: {e}")
            raise

def get_bucket(s3, bucket_name: str) -> dict:
    """ Retrieve metadata about an S3 bucket. """
    try:
        bucket_info = s3.get_bucket_acl(Bucket=bucket_name)
        logger.info(f"Retrieved bucket {bucket_name} information successfully.")
        return bucket_info
    except ClientError as e:
        logger.error(f"Error retrieving information for bucket {bucket_name}: {e}")
        raise

def get_bucket_arn(bucket_name: str) -> str:
    """ Generate the ARN for an S3 bucket based on its name. """
    return f"arn:aws:s3:::{bucket_name}"

def delete_bucket(s3, bucket_name: str):
    try:
        s3.delete_bucket(Bucket=bucket_name)
        logger.info(f"Bucket {bucket_name} deleted successfully.")
    except ClientError as e:
        logger.error(f"Error deleting bucket {bucket_name}: {e}")
        raise

def list_buckets(s3) -> list[dict]:
    try:
        response = s3.list_buckets()
        return [
            {"name": bucket["Name"], "creation_date": bucket["CreationDate"]}
            for bucket in response["Buckets"]
        ]
    except ClientError as e:
        logger.error(f"Error listing buckets: {e}")
        raise
