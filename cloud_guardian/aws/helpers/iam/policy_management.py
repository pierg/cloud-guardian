import json

from botocore.exceptions import ClientError
from cloud_guardian import logger


def create_policy(iam, policy_name: str, policy_document: dict) -> str:
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


def get_policy_document(iam, policy_arn: str) -> dict:
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


def get_policy_from_name(iam, policy_name: str) -> dict:
    """Retrieve the policy ARN and document for a given policy name."""
    try:
        # Use a paginator to handle pagination
        paginator = iam.get_paginator("list_policies")
        for page in paginator.paginate(Scope="Local"):
            for policy in page["Policies"]:
                if policy["PolicyName"] == policy_name:
                    policy_arn = policy["Arn"]
                    # Retrieve the policy document
                    policy_document = get_policy_document(iam, policy_arn)
                    return {"PolicyArn": policy_arn, "PolicyDocument": policy_document}
        logger.warning(f"No policy found with name {policy_name}")
    except ClientError as e:
        logger.error(f"Error searching for policy named {policy_name}: {e}")
        raise e


def delete_policy(iam, policy_arn: str):
    try:
        iam.delete_policy(PolicyArn=policy_arn)
        logger.info(f"Policy {policy_arn} deleted successfully.")
    except ClientError as e:
        logger.error(f"Error deleting policy {policy_arn}: {e}")
        raise e


def attach_policy_to_user(iam, policy_arn: str, user_name: str):
    try:
        iam.attach_user_policy(UserName=user_name, PolicyArn=policy_arn)
        logger.info(f"Policy {policy_arn} attached to user {user_name}")
    except ClientError as e:
        logger.error(f"Error attaching policy to user {user_name}: {e}")
        raise e


def detach_policy_from_user(iam, policy_arn: str, user_name: str):
    try:
        iam.detach_user_policy(UserName=user_name, PolicyArn=policy_arn)
        logger.info(f"Policy {policy_arn} detached from user {user_name}.")
    except ClientError as e:
        logger.error(f"Error detaching policy from user {user_name}: {e}")
        raise e


def attach_policy_to_group(iam, policy_arn: str, group_name: str):
    try:
        iam.attach_group_policy(GroupName=group_name, PolicyArn=policy_arn)
        logger.info(f"Policy {policy_arn} attached to group {group_name}")
    except ClientError as e:
        logger.error(f"Error attaching policy to group {group_name}: {e}")
        raise e


def detach_policy_from_group(iam, policy_arn: str, group_name: str):
    try:
        iam.detach_group_policy(GroupName=group_name, PolicyArn=policy_arn)
        logger.info(f"Policy {policy_arn} detached from group {group_name}.")
    except ClientError as e:
        logger.error(f"Error detaching policy from group {group_name}: {e}")
        raise e
