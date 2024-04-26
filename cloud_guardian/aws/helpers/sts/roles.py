from botocore.exceptions import ClientError
from cloud_guardian import logger


def assume_role(
    sts,
    role_arn: str,
    role_session_name: str = "role_session",
    duration_seconds: int = 3600,
) -> dict:
    try:
        # Assuming the role via STS and retrieving temporary credentials
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=role_session_name,
            DurationSeconds=duration_seconds,
        )
        # Extracting the credentials from the response
        credentials = response["Credentials"]
        logger.info(
            f"Successfully assumed role {role_arn} with session name {role_session_name}."
        )
        return credentials
    except ClientError as e:
        logger.error(f"Failed to assume role {role_arn}: {e}")
        raise e
