from pathlib import Path

import boto3
from botocore.credentials import ReadOnlyCredentials
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
from cloud_guardian.utils.loaders import (
    load_iam_data_into_dictionaries,
)
from cloud_guardian.utils.maps import (
    BiMap,
    get_all_principals_ids,
    get_all_resources_ids,
    update_arns,
)
from cloud_guardian.utils.strings import get_name_and_type_from_id, pretty_print, strip_s3_resource_id


class AWSManager:
    def __init__(self, region_name="us-east-1"):
        self.region_name = region_name
        self.session = boto3.Session(region_name=self.region_name)
        self.credentials = {}  # Stores credentials indexed by ARN or 'default'
        self.store_credentials(
            "default", self.session.get_credentials().get_frozen_credentials()
        )
        self.refresh_clients()

    def store_credentials(self, identity_arn, credentials):
        """Store credentials under a given ARN"""
        if credentials:
            if isinstance(credentials, ReadOnlyCredentials):
                # Handle ReadOnlyCredentials format
                stored_creds = {
                    "access_key": credentials.access_key,
                    "secret_key": credentials.secret_key,
                    "session_token": credentials.token,
                }
            elif isinstance(credentials, dict):
                # Handle dictionary format (typically from assume_role)
                stored_creds = {
                    "access_key": credentials.get("AccessKeyId"),
                    "secret_key": credentials.get("SecretAccessKey"),
                    "session_token": credentials.get("SessionToken"),
                }
            else:
                logger.error(f"No valid credentials found for {identity_arn}.")
                raise ValueError("Unsupported credential format provided.")

            # Save the processed credentials
            self.credentials[identity_arn] = stored_creds
            logger.info(f"Credentials stored for {identity_arn}.")
        else:
            logger.error(f"No valid credentials found for {identity_arn}.")
            raise ValueError("No valid credentials provided.")

    def refresh_clients(self):
        """Refresh AWS service clients with the current session"""
        self.iam = self.session.client("iam")
        self.s3 = self.session.client("s3")
        self.sts = self.session.client("sts")

    def set_identity(self, identity_arn):
        """Set the AWS identity by ARN and update the session using stored credentials"""
        if identity_arn in self.credentials:
            creds = self.credentials[identity_arn]
            self.session = boto3.Session(
                aws_access_key_id=creds["access_key"],
                aws_secret_access_key=creds["secret_key"],
                aws_session_token=creds["session_token"],
                region_name=self.region_name,
            )
            self.refresh_clients()
            logger.info(f"Identity set to {identity_arn}.")
        else:
            raise ValueError("No credentials stored for this ARN")

    def import_from_json(self, folder_path: Path):
        """Import IAM and S3 configurations from JSON files and create AWS resources"""
        groups_dict, policies_dict, roles_dict, users_dict = (
            load_iam_data_into_dictionaries(folder_path)
        )

        bi_map = BiMap()

        # Create identity-based policies and attach them to the identities
        for policy in policies_dict["IdentityBasedPolicies"]:
            policy_name = get_name_and_type_from_id(policy["ID"])[0]
            policy_arn = create_policy(self.iam, policy_name, policy["PolicyDocument"])
            bi_map.add(policy_arn, policy["ID"])

        # Create groups and attach policies
        for group in groups_dict["Groups"]:
            group_name = get_name_and_type_from_id(group["ID"])[0]
            group_arn = create_group(self.iam, group_name)
            logger.warning("GROUP CREATED WITH ARN: " + group_arn)
            bi_map.add(group_arn, group["ID"])
            for policy in group["AttachedPolicies"]:
                policy_arn = bi_map.get_arn(policy["ID"])
                attach_policy_to_group(self.iam, policy_arn, group_name)

        # Create users, attach policies
        for user in users_dict["Users"]:
            user_name = get_name_and_type_from_id(user["ID"])[0]
            user_info = create_user_and_access_keys(self.iam, user_name)
            user_arn = user_info["Arn"]
            self.credentials[user_arn] = (
                user_info["AccessKeyId"],
                user_info["SecretAccessKey"],
            )
            bi_map.add(user_arn, user["ID"])
            for policy in user.get("AttachedPolicies", []):
                policy_arn = bi_map.get_arn(policy["ID"])
                attach_policy_to_user(self.iam, policy_arn, user_name)

        # Add users to groups
        for group in groups_dict["Groups"]:
            group_name = get_name_and_type_from_id(group["ID"])[0]
            for user in group["Users"]:
                user_name = get_name_and_type_from_id(bi_map.get_arn(user["ID"]))[0]
                add_user_to_group(self.iam, user_name, group_name)

        # Create roles and attach policies
        for role in roles_dict["Roles"]:
            role_name = get_name_and_type_from_id(role["ID"])[0]
            role_arn = create_role(
                self.iam, role_name, role["AssumeRolePolicyDocument"]
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
                            self.iam, principal_name
                        )["Arn"]
                        principal_arn = principal_info["Arn"]
                        self.credentials[principal_arn] = (
                            principal_info["AccessKeyId"],
                            principal_info["SecretAccessKey"],
                        )
                        bi_map.add(user_arn, user["ID"])
                    elif principal_type == "group":
                        principal_arn = create_group(self.iam, principal_name)
                    elif principal_type == "role":
                        principal_arn = create_role(self.iam, principal_name, {})
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
                        bucket_name = create_bucket(self.s3, resource_name)
                        bucket_arn = get_bucket_arn(bucket_name)
                        bi_map.add(bucket_arn, strip_s3_resource_id(resource_id))
                    else:
                        raise ValueError("Resource type not recognized.")

            pretty_print(policy)
            update_arns(policy, bi_map)
            pretty_print(policy)
            set_bucket_policy(self.s3, resource_name, policy)

    def export_to_json(self, folder_path: Path):
        pass
        # Not needed for now
