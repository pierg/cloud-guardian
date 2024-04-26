from botocore.exceptions import ClientError
from cloud_guardian import logger


def get_identity_or_resource_from_arn(arn: str, iam=None, s3=None):
    try:
        parts = arn.split(":")
        if len(parts) < 6:
            raise ValueError("Invalid ARN format")

        service = parts[2]  # Service (e.g., s3, iam)
        resource_part = parts[5]
        # Resource type (e.g., user, role, bucket)
        resource_type = resource_part.split("/")[0]
        resource_name = (
            "/".join(resource_part.split("/")[1:]) if "/" in resource_part else None
        )

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
            if resource_type == "bucket":
                # S3 does not have a specific API to get bucket details by ARN, so we return the name
                logger.info(f"Retrieved details for S3 bucket: {resource_name}")
                return {"BucketName": resource_name}
            else:
                raise ValueError(
                    f"Unsupported S3 resource type '{resource_type}' in ARN"
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
