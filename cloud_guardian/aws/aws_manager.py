from pathlib import Path

import boto3
from cloud_guardian.aws.helpers.iam.group_management import create_group
from cloud_guardian.aws.helpers.iam.policy_management import (
    attach_policy_to_group,
    attach_policy_to_user,
    create_policy,
)
from cloud_guardian.aws.helpers.iam.role_management import create_role
from cloud_guardian.aws.helpers.iam.user_management import (
    add_user_to_group,
    create_user,
)
from cloud_guardian.aws.helpers.s3.bucket_operations import create_bucket
from cloud_guardian.aws.helpers.s3.bucket_policy import set_bucket_policy
from cloud_guardian.utils.loaders import (
    extract_bucket_names,
    load_iam_data_into_dictionaries,
)
from cloud_guardian.utils.maps import BiMap
from cloud_guardian.utils.strings import get_name_from_arn


class AWSManager:
    def __init__(
        self,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        region_name="us-east-1",
    ):
        self.iam = boto3.client(
            "iam",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    def import_from_json(self, folder_path: Path):
        groups_dict, policies_dict, roles_dict, users_dict = (
            load_iam_data_into_dictionaries(folder_path)
        )

        bi_map = BiMap()

        # Create identity-based policies and attach them to the identities
        for policy in policies_dict["IdentityBasedPolicies"]:
            policy_name = get_name_from_arn(policy["ID"])
            policy_arn = create_policy(self.iam, policy_name, policy["PolicyDocument"])
            bi_map.add(policy_arn, policy["ID"])

        # Create groups and attach policies
        for group in groups_dict["Groups"]:
            group_name = get_name_from_arn(group["ID"])
            group_arn = create_group(self.iam, group_name)
            bi_map.add(group_arn, group["ID"])
            for policy in group["AttachedPolicies"]:
                policy_arn = bi_map.get(policy["ID"])
                attach_policy_to_group(self.iam, policy_arn, group_name)

        # Create users, attach policies
        for user in users_dict["Users"]:
            user_name = get_name_from_arn(user["ID"])
            user_arn = create_user(self.iam, user_name)
            bi_map.add(user_arn, user["ID"])
            for policy in user.get("AttachedPolicies", []):
                policy_arn = bi_map.get(policy["ID"])
                attach_policy_to_user(self.iam, policy_arn, user_name)

        # Add users to groups
        for group in groups_dict["Groups"]:
            group_name = get_name_from_arn(group["ID"])
            for user in group["Users"]:
                user_name = get_name_from_arn(bi_map.get(user["ID"]))
                add_user_to_group(self.iam, user_name, group_name)

        # Create roles and attach policies
        for role in roles_dict["Roles"]:
            role_name = get_name_from_arn(role["ID"])
            role_arn = create_role(
                self.iam, role_name, role["AssumeRolePolicyDocument"]
            )
            bi_map.add(role_arn, role["ID"])

        # # Process resource-based policies
        for policy in policies_dict["ResourceBasedPolicies"]:
            for resource_name in extract_bucket_names(policy):
                create_bucket(self.s3, resource_name)
                set_bucket_policy(self.s3, resource_name, policy["PolicyDocument"])

    def export_to_json(self, folder_path: Path):
        pass
        # Not needed for now
        # try:
        #     users = self.iam.list_users()['Users']
        #     groups = self.iam.list_groups()['Groups']
        #     policies = self.iam.list_policies(Scope='Local')['Policies']
        #     roles = self.iam.list_roles()['Roles']

        #     export_data = {
        #         'users': [{'name': user['UserName']} for user in users],
        #         'groups': [{'name': group['GroupName']} for group in groups],
        #         'policies': [{'name': policy['PolicyName'], 'arn': policy['Arn']} for policy in policies],
        #         'roles': [{'name': role['RoleName']} for role in roles]
        #     }
        #     return json.dumps(export_data, indent=4)
        # except ClientError as e:
        #     logger.error(f"Failed to export to JSON: {e}")
        #     raise
