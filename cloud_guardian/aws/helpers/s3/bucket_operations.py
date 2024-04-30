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
        logger.info(f"Bucket {bucket_name} created successfully.")
        return bucket_name
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "BucketAlreadyExists":
            logger.warning(
                f"Bucket {bucket_name} already exists and is owned by another user."
            )
            return bucket_name
        else:
            logger.error(f"Error creating bucket {bucket_name}: {e}")
            raise


def get_bucket_info(s3, bucket_name: str) -> dict:
    """Retrieve metadata about an S3 bucket, like: name, creation date, owner, ARN, and service."""
    try:
        all_buckets = s3.list_buckets()
        bucket_info = next(
            (
                bucket
                for bucket in all_buckets["Buckets"]
                if bucket["Name"] == bucket_name
            ),
            None,
        )
        if bucket_info is None:
            logger.error(f"Bucket {bucket_name} not found.")
            raise Exception("Bucket not found")

        response = s3.get_bucket_acl(Bucket=bucket_name)
        owner = response["Owner"]
        bucket_arn = f"arn:aws:s3:::{bucket_name}"

        logger.info(
            f"Retrieved bucket {bucket_name} information successfully: Owner {owner}, Created on {bucket_info['CreationDate']}, ARN {bucket_arn}"
        )
        return {
            "Name": bucket_name,
            "CreateDate": bucket_info["CreationDate"],
            "Owner": owner,
            "ARN": bucket_arn,
            "Service": "s3",
        }
    except ClientError as e:
        logger.error(f"Error retrieving information for bucket {bucket_name}: {e}")
        raise


def get_bucket(s3, bucket_name: str) -> dict:
    """Retrieve metadata about an S3 bucket."""
    try:
        bucket_info = s3.get_bucket_acl(Bucket=bucket_name)
        logger.info(f"Retrieved bucket {bucket_name} information successfully.")
        return bucket_info
    except ClientError as e:
        logger.error(f"Error retrieving information for bucket {bucket_name}: {e}")
        raise


def get_bucket_arn(bucket_name: str) -> str:
    """Generate the ARN for an S3 bucket based on its name."""
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
