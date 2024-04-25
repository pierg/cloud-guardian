import json
from typing import Dict, List, Optional

from botocore.exceptions import ClientError
from loguru import logger


def create_policy(iam, policy_name: str, policy_document: dict) -> Optional[str]:
    """
    Create an IAM policy and return its ARN.
    """
    try:
        response = iam.create_policy(
            PolicyName=policy_name, PolicyDocument=json.dumps(policy_document)
        )
        logger.info(
            f"Policy {policy_name} created with ARN: {response['Policy']['Arn']}"
        )
        return response["Policy"]["Arn"]
    except ClientError as e:
        logger.error(f"Error creating policy {policy_name}: {e}")
        raise e


def get_policy_document(iam, policy_arn: str) -> Optional[dict]:
    """
    Get the policy document for an IAM policy.
    """
    try:
        response = iam.get_policy(PolicyArn=policy_arn)
        policy_version_id = response["Policy"]["DefaultVersionId"]
        version_response = iam.get_policy_version(
            PolicyArn=policy_arn, VersionId=policy_version_id
        )
        logger.info(f"Policy document retrieved for {policy_arn}")
        return version_response["PolicyVersion"]["Document"]
    except ClientError as e:
        logger.error(f"Error retrieving policy document for ARN {policy_arn}: {e}")
        raise e


def create_user(iam, user_name: str) -> Optional[str]:
    """
    Create an IAM user and return the ARN.
    """
    try:
        response = iam.create_user(UserName=user_name)
        logger.info(f"User {user_name} created with ARN: {response['User']['Arn']}")
        return response["User"]["Arn"]
    except ClientError as e:
        logger.error(f"Error creating user {user_name}: {e}")
        raise e


def create_group(iam, group_name: str) -> Optional[str]:
    """
    Create an IAM group and return the ARN.
    """
    try:
        response = iam.create_group(GroupName=group_name)
        logger.info(f"Group {group_name} created with ARN: {response['Group']['Arn']}")
        return response["Group"]["Arn"]
    except ClientError as e:
        logger.error(f"Error creating group {group_name}: {e}")
        raise e


def add_user_to_group(iam, user_name: str, group_name: str) -> bool:
    """
    Add a user to an IAM group.
    """
    try:
        iam.add_user_to_group(GroupName=group_name, UserName=user_name)
        logger.info(f"User {user_name} added to group {group_name}")
        return True
    except ClientError as e:
        logger.error(f"Error adding user {user_name} to group {group_name}: {e}")
        return False


def attach_policy_to_user(iam, policy_arn: str, user_name: str) -> bool:
    """
    Attach a policy to an IAM user.
    """
    try:
        iam.attach_user_policy(UserName=user_name, PolicyArn=policy_arn)
        logger.info(f"Policy {policy_arn} attached to user {user_name}")
        return True
    except ClientError as e:
        logger.error(f"Error attaching policy to user {user_name}: {e}")
        return False


def attach_policy_to_group(iam, policy_arn: str, group_name: str) -> bool:
    """
    Attach a policy to an IAM group.
    """
    try:
        iam.attach_group_policy(GroupName=group_name, PolicyArn=policy_arn)
        logger.info(f"Policy {policy_arn} attached to group {group_name}")
        return True
    except ClientError as e:
        logger.error(f"Error attaching policy to group {group_name}: {e}")
        raise e


def create_role(iam, role_name: str, assume_role_policy: dict) -> Optional[str]:
    """
    Create an IAM role and return the ARN.
    """
    try:
        response = iam.create_role(
            RoleName=role_name, AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )
        logger.info(f"Role {role_name} created with ARN: {response['Role']['Arn']}")
        return response["Role"]["Arn"]
    except ClientError as e:
        logger.error(f"Error creating role {role_name}: {e}")
        raise e


def delete_user(iam, user_name: str) -> bool:
    """
    Delete an IAM user.
    """
    try:
        iam.delete_user(UserName=user_name)
        logger.info(f"User {user_name} deleted successfully.")
        return True
    except ClientError as e:
        logger.error(f"Error deleting user {user_name}: {e}")
        return False


def delete_group(iam, group_name: str) -> bool:
    """
    Delete an IAM group.
    """
    try:
        iam.delete_group(GroupName=group_name)
        logger.info(f"Group {group_name} deleted successfully.")
        return True
    except ClientError as e:
        logger.error(f"Error deleting group {group_name}: {e}")
        return False


def delete_policy(iam, policy_arn: str) -> bool:
    """
    Delete an IAM policy.
    """
    try:
        iam.delete_policy(PolicyArn=policy_arn)
        logger.info(f"Policy {policy_arn} deleted successfully.")
        return True
    except ClientError as e:
        logger.error(f"Error deleting policy {policy_arn}: {e}")
        return False


def delete_role(iam, role_name: str) -> bool:
    """
    Delete an IAM role.
    """
    try:
        iam.delete_role(RoleName=role_name)
        logger.info(f"Role {role_name} deleted successfully.")
        return True
    except ClientError as e:
        logger.error(f"Error deleting role {role_name}: {e}")
        return False


def detach_policy_from_user(iam, policy_arn: str, user_name: str) -> bool:
    """
    Detach a policy from an IAM user.
    """
    try:
        iam.detach_user_policy(UserName=user_name, PolicyArn=policy_arn)
        logger.info(f"Policy {policy_arn} detached from user {user_name}.")
        return True
    except ClientError as e:
        logger.error(f"Error detaching policy from user {user_name}: {e}")
        return False


def detach_policy_from_group(iam, policy_arn: str, group_name: str) -> bool:
    """
    Detach a policy from an IAM group.
    """
    try:
        iam.detach_group_policy(GroupName=group_name, PolicyArn=policy_arn)
        logger.info(f"Policy {policy_arn} detached from group {group_name}.")
        return True
    except ClientError as e:
        logger.error(f"Error detaching policy from group {group_name}: {e}")
        return False


def list_attached_user_policies(iam, user_name: str) -> List[Dict[str, str]]:
    """
    List all policies attached to a specific IAM user.
    """
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
        return []


def check_role_exists(iam, role_name: str) -> bool:
    """
    Check if a specific IAM role exists.
    """
    try:
        iam.get_role(RoleName=role_name)
        logger.info(f"Role {role_name} exists.")
        return True
    except ClientError as e:
        logger.error(f"Role {role_name} does not exist: {e}")
        return False


def get_principals_for_role(iam, role_name: str) -> List[str]:
    """
    Get the principals that can assume a role.
    """
    try:
        response = iam.get_role(RoleName=role_name)

        policy_document = response["Role"]["AssumeRolePolicyDocument"]
        principals = [
            statement["Principal"]["ID"] for statement in policy_document["Statement"]
        ]
        return principals
    except ClientError as e:
        logger.error(f"Error retrieving role {role_name}: {e}")
        raise e
