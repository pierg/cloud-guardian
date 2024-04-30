from arnparse import arnparse
from botocore.exceptions import ClientError
from cloud_guardian import logger
from cloud_guardian.aws.helpers.s3.bucket_operations import get_bucket_info


def get_identity_or_resource_from_arn(arn: str, iam=None, s3=None):
    try:
        parsed_arn = arnparse(arn)

        service = parsed_arn.service  # e.g., "s3" or "iam"
        resource_type = parsed_arn.resource_type  # e.g., "user", "group"
        resource_name = (
            parsed_arn.resource
        )  # e.g., "bucket-name" for S3 or "user-name" for IAM
        if service == "iam" and iam:
            if resource_type == "user":
                response = iam.get_user(UserName=resource_name)
                logger.info(f"Retrieved details for IAM user: {resource_name}")
                return response["User"]
            elif resource_type == "group":
                response = iam.get_group(GroupName=resource_name)
                logger.info(f"Retrieved details for IAM group: {resource_name}")
                return response["Group"]
            elif resource_type == "role":
                response = iam.get_role(RoleName=resource_name)
                logger.info(f"Retrieved details for IAM role: {resource_name}")
                return response["Role"]
            else:
                raise ValueError(
                    f"Unsupported IAM resource type '{resource_type}' in ARN"
                )
        elif service == "s3" and s3:
            return get_bucket_info(
                s3,
                resource_name.split("/")[0] if "/" in resource_name else resource_name,
            )
        else:
            raise ValueError(
                f"Unsupported service '{service}' or service client not provided in ARN"
            )

    except ClientError as e:
        logger.error(f"Error retrieving identity or resource from ARN {arn}: {e}")
        raise e
    except ValueError as e:
        logger.error(f"Error parsing ARN {arn}: {e}")
        raise e


# TEST
# from cloud_guardian.aws.helpers.s3.bucket_operations import create_bucket, get_bucket
# from moto import mock_aws
# import boto3
# mock = mock_aws()
# mock.start()
# session = boto3.Session(region_name="us-east-1")

# iam = session.client("iam")
# s3 = session.client("s3")

# test_str = "arn:aws:s3:::company-files/*"
# parsed_arn = arnparse(test_str)
# print(parsed_arn)
# print(parsed_arn.service)
# print(parsed_arn.resource)
# create_bucket(s3, "company-files")
# print(get_identity_or_resource_from_arn(test_str, iam=iam, s3=s3))
