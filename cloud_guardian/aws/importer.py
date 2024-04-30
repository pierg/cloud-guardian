from abc import ABC, abstractmethod
from pathlib import Path

import joblib
import pandas as pd
from cloud_guardian import logger
from cloud_guardian.aws.helpers.iam.group_management import create_group
from cloud_guardian.aws.helpers.iam.policy_management import (
    attach_policy_to_group,
    attach_policy_to_user,
    create_policy,
)
from cloud_guardian.aws.helpers.iam.role_management import create_role
from cloud_guardian.aws.helpers.iam.user_management import (
    add_user_to_group,
    create_user_and_access_keys,
)
from cloud_guardian.aws.helpers.s3.bucket_operations import (
    create_bucket,
    get_bucket_arn,
)
from cloud_guardian.aws.helpers.s3.bucket_policy import set_bucket_policy
from cloud_guardian.utils.loaders import load_iam_data_into_dictionaries
from cloud_guardian.utils.maps import (
    BiMap,
    get_all_principals_ids,
    get_all_resources_ids,
    update_arns,
)
from cloud_guardian.utils.strings import (
    get_name_and_type_from_id,
    strip_s3_resource_id,
)
from cloud_guardian.utils.tuple_repr import Tuples


class Importer(ABC):
    @abstractmethod
    def import_data(self, folder_path: Path, aws_manager):
        pass


class JsonImporter(Importer):
    def import_data(self, folder_path: Path, aws_manager):
        """Import IAM and S3 configurations from JSON files and create AWS resources"""
        groups_dict, policies_dict, roles_dict, users_dict = (
            load_iam_data_into_dictionaries(folder_path)
        )

        bi_map = BiMap()

        # Create identity-based policies and attach them to the identities
        for policy in policies_dict["IdentityBasedPolicies"]:
            policy_name = get_name_and_type_from_id(policy["ID"])[0]
            policy_arn = create_policy(
                aws_manager.iam, policy_name, policy["PolicyDocument"]
            )
            bi_map.add(policy_arn, policy["ID"])

        # Create groups and attach policies
        for group in groups_dict["Groups"]:
            group_name = get_name_and_type_from_id(group["ID"])[0]
            group_arn = create_group(aws_manager.iam, group_name)
            bi_map.add(group_arn, group["ID"])
            for policy in group["AttachedPolicies"]:
                policy_arn = bi_map.get_arn(policy["ID"])
                attach_policy_to_group(aws_manager.iam, policy_arn, group_name)

        # Create users, attach policies
        for user in users_dict["Users"]:
            user_name = get_name_and_type_from_id(user["ID"])[0]
            user_info = create_user_and_access_keys(aws_manager.iam, user_name)
            user_arn = user_info["Arn"]
            aws_manager.credentials[user_arn] = (
                user_info["AccessKeyId"],
                user_info["SecretAccessKey"],
            )
            bi_map.add(user_arn, user["ID"])
            for policy in user.get("AttachedPolicies", []):
                policy_arn = bi_map.get_arn(policy["ID"])
                attach_policy_to_user(aws_manager.iam, policy_arn, user_name)

        # Add users to groups
        for group in groups_dict["Groups"]:
            group_name = get_name_and_type_from_id(group["ID"])[0]
            for user in group["Users"]:
                user_name = get_name_and_type_from_id(bi_map.get_arn(user["ID"]))[0]
                add_user_to_group(aws_manager.iam, user_name, group_name)

        # Create roles and attach policies
        for role in roles_dict["Roles"]:
            role_name = get_name_and_type_from_id(role["ID"])[0]
            role_arn = create_role(
                aws_manager.iam, role_name, role["AssumeRolePolicyDocument"]
            )
            bi_map.add(role_arn, role["ID"])

        # # Process resource-based policies
        for policy in policies_dict["ResourceBasedPolicies"]:
            principals = get_all_principals_ids(policy)
            for principal_id in principals:
                principal_arn = bi_map.get_arn(principal_id)
                if principal_arn is None:
                    logger.warning(
                        f"Principal {principal_id} not found in BiMap. Creating identity now..."
                    )
                    principal_name, principal_type = get_name_and_type_from_id(
                        principal_id
                    )
                    logger.info(f"Creating {principal_type} {principal_name}")
                    if principal_type == "user":
                        principal_info = create_user_and_access_keys(
                            aws_manager.iam, principal_name
                        )["Arn"]
                        principal_arn = principal_info["Arn"]
                        aws_manager.credentials[principal_arn] = (
                            principal_info["AccessKeyId"],
                            principal_info["SecretAccessKey"],
                        )
                        bi_map.add(user_arn, user["ID"])
                    elif principal_type == "group":
                        principal_arn = create_group(aws_manager.iam, principal_name)
                    elif principal_type == "role":
                        principal_arn = create_role(aws_manager.iam, principal_name, {})
                    else:
                        raise ValueError("Principal type not recognized.")
                    bi_map.add(principal_id, principal_arn)
            resources_ids = get_all_resources_ids(policy)
            for resource_id in resources_ids:
                resource_id = strip_s3_resource_id(resource_id)
                if bi_map.get_arn(resource_id) is None:
                    resource_name, resource_type = get_name_and_type_from_id(
                        resource_id
                    )
                    if resource_type == "s3":
                        bucket_name = create_bucket(aws_manager.s3, resource_name)
                        bucket_arn = get_bucket_arn(bucket_name)
                        bi_map.add(bucket_arn, strip_s3_resource_id(resource_id))
                    else:
                        raise ValueError("Resource type not recognized.")

            update_arns(policy, bi_map)
            set_bucket_policy(aws_manager.s3, resource_name, policy)


class DFImporter(Importer):
    def import_data(self, folder_path: Path, aws_manager):
        data = joblib.load(folder_path / "data.joblib")
        df = pd.DataFrame(data)
        tuples = Tuples.from_df(df)

        bi_map = BiMap()

        # Create all users
        for user in tuples.users.values():
            user_info = create_user_and_access_keys(aws_manager.iam, user.id)
            user_arn = user_info["Arn"]
            aws_manager.credentials[user_arn] = (
                user_info["AccessKeyId"],
                user_info["SecretAccessKey"],
            )
            bi_map.add(user_arn, user.id)

        # Create all groups and add users
        for group in tuples.groups.values():
            group_arn = create_group(aws_manager.iam, group.id)
            bi_map.add(group_arn, group.id)

        # Add users to groups
        for group_id, users in tuples.group_to_users.items():
            for user in users:
                user_name = get_name_and_type_from_id(bi_map.get_arn(user))[0]
                add_user_to_group(aws_manager.iam, user_name, group_id)

        # Create all roles and attach policies
        for role in tuples.roles.values():
            role_arn = create_role(
                aws_manager.iam, role.name, tuples.roles_to_policy_document[role.id]
            )
            bi_map.add(role_arn, role.id)

        # Process all permissions
        for permission in tuples.permissions:
            source_arn = bi_map.get_arn(permission.source.id)
            target_arn = bi_map.get_arn(permission.target.id)
            if source_arn is None:
                raise ValueError(f"Source {permission.source.id} not found in BiMap")
            if target_arn is None:
                raise ValueError(f"Target {permission.target.id} not found in BiMap")
            create_policy(
                aws_manager.iam, permission.action, permission.to_policy_document()
            )
