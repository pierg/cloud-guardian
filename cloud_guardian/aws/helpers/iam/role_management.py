import json

from botocore.exceptions import ClientError
from cloud_guardian import logger


def create_role(iam, role_name: str, assume_role_policy: dict) -> str:
    try:
        response = iam.create_role(
            RoleName=role_name, AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )
        logger.info(f"Role {role_name} created with ARN: {response['Role']['Arn']}")
        return response["Role"]["Arn"]
    except ClientError as e:
        logger.error(f"Error creating role {role_name}: {e}")
        raise e


def delete_role(iam, role_name: str):
    try:
        iam.delete_role(RoleName=role_name)
        logger.info(f"Role {role_name} deleted successfully.")
        return True
    except ClientError as e:
        logger.error(f"Error deleting role {role_name}: {e}")
        raise e


def does_role_exists(iam, role_name: str) -> bool:
    try:
        iam.get_role(RoleName=role_name)
        logger.info(f"Role {role_name} exists.")
        return True
    except ClientError as e:
        logger.info(f"Role {role_name} does not exist: {e}")
        return False


def get_principals_for_role(iam, role_name: str) -> list[str]:
    try:
        response = iam.get_role(RoleName=role_name)
        policy_document = response["Role"]["AssumeRolePolicyDocument"]
        # TODO not now:
        # in real aws policies there is no "ID" key in the Principal object, this is a mockup, ok for now
        principals = [
            statement["Principal"]["ID"] for statement in policy_document["Statement"]
        ]
        return principals
    except ClientError as e:
        logger.error(f"Error retrieving principals for role {role_name}: {e}")
        raise e
