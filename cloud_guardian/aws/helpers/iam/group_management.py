from botocore.exceptions import ClientError
from cloud_guardian import logger


def create_group(iam, group_name: str) -> str:
    try:
        response = iam.create_group(GroupName=group_name)
        logger.info(f"Group {group_name} created with ARN: {response['Group']['Arn']}")
        return response["Group"]["Arn"]
    except ClientError as e:
        logger.error(f"Error creating group {group_name}: {e}")
        raise e


def get_group(iam, group_name: str) -> dict:
    try:
        response = iam.get_group(GroupName=group_name)
        return response["Group"]
    except ClientError as e:
        logger.error(f"Error retrieving group {group_name}: {e}")
        raise e


def delete_group(iam, group_name: str):
    try:
        iam.delete_group(GroupName=group_name)
        logger.info(f"Group {group_name} deleted successfully.")
    except ClientError as e:
        logger.error(f"Error deleting group {group_name}: {e}")
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
