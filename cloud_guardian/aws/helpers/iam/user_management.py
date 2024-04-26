from botocore.exceptions import ClientError
from cloud_guardian import logger


def create_user_and_access_keys(iam, user_name: str):
    """
    Creates an IAM user and generates access keys for that user.

    Args:
        iam: An IAM service client instance of boto3.
        user_name: The name of the user to create.

    Returns:
        A dictionary containing the user's ARN and access keys, or raises an error.

    Raises:
        ClientError: An error occurred when attempting to create the user or the access keys.
    """
    try:
        # Create the user
        user_response = iam.create_user(UserName=user_name)
        user_arn = user_response["User"]["Arn"]
        logger.info(f"User {user_name} created with ARN: {user_arn}")

        # Create access keys for the user
        keys_response = iam.create_access_key(UserName=user_name)
        access_key_id = keys_response["AccessKey"]["AccessKeyId"]
        secret_access_key = keys_response["AccessKey"]["SecretAccessKey"]
        logger.info(f"Access keys created for user {user_name}")

        return {
            "Arn": user_arn,
            "AccessKeyId": access_key_id,
            "SecretAccessKey": secret_access_key,
        }

    except ClientError as e:
        logger.error(f"Error in creating user {user_name} or access keys: {e}")
        raise


def get_user(iam, user_name: str) -> dict:
    try:
        response = iam.get_user(UserName=user_name)
        return response["User"]
    except ClientError as e:
        logger.error(f"Error retrieving ARN for user {user_name}: {e}")
        raise e


def delete_user(iam, user_name: str):
    try:
        iam.delete_user(UserName=user_name)
        logger.info(f"User {user_name} deleted successfully.")
    except ClientError as e:
        logger.error(f"Error deleting user {user_name}: {e}")
        raise e


def add_user_to_group(iam, user_name: str, group_name: str):
    try:
        iam.add_user_to_group(GroupName=group_name, UserName=user_name)
        logger.info(f"User {user_name} added to group {group_name}")
    except ClientError as e:
        logger.error(f"Error adding user {user_name} to group {group_name}: {e}")
        raise e


def list_attached_user_policies(iam, user_name: str) -> list[dict]:
    try:
        paginator = iam.get_paginator("list_attached_user_policies")
        response_iterator = paginator.paginate(UserName=user_name)
        policies = []
        for response in response_iterator:
            for policy in response["AttachedPolicies"]:
                policies.append(
                    {"arn": policy["PolicyArn"], "name": policy["PolicyName"]}
                )
        logger.info(f"Listed attached policies for user {user_name}.")
        return policies
    except ClientError as e:
        logger.error(f"Error listing attached policies for user {user_name}: {e}")
        raise e


def detach_policy_from_user(iam, policy_arn: str, user_name: str):
    try:
        iam.detach_user_policy(UserName=user_name, PolicyArn=policy_arn)
        logger.info(f"Policy {policy_arn} detached from user {user_name}.")
    except ClientError as e:
        logger.error(f"Error detaching policy from user {user_name}: {e}")
        raise e
