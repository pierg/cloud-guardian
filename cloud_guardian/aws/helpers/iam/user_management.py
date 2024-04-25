from botocore.exceptions import ClientError
from cloud_guardian import logger


def create_user(iam, user_name: str) -> str:
    try:
        response = iam.create_user(UserName=user_name)
        logger.info(f"User {user_name} created with ARN: {response['User']['Arn']}")
        return response["User"]["Arn"]
    except ClientError as e:
        logger.error(f"Error creating user {user_name}: {e}")
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
