from botocore.exceptions import ClientError
from cloud_guardian import logger


def create_bucket(s3, bucket_name: str, region: str = None) -> str:
    try:
        if region:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
        else:
            s3.create_bucket(Bucket=bucket_name)
        logger.info(f"Bucket {bucket_name} created")
        return bucket_name
    except ClientError as e:
        logger.error(f"Error creating bucket {bucket_name}: {e}")
        raise e


def delete_bucket(s3, bucket_name: str):
    try:
        s3.delete_bucket(Bucket=bucket_name)
        logger.info(f"Bucket {bucket_name} deleted")
    except ClientError as e:
        logger.error(f"Error deleting bucket {bucket_name}: {e}")
        raise e


def list_buckets(s3) -> list[dict]:
    try:
        response = s3.list_buckets()
        return [
            {"name": bucket["Name"], "creation_date": bucket["CreationDate"]}
            for bucket in response["Buckets"]
        ]
    except ClientError as e:
        logger.error("Error listing buckets: {e}")
        raise e
