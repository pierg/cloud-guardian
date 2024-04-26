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
from cloud_guardian.aws.helpers.s3.bucket_operations import create_bucket
from cloud_guardian.aws.helpers.s3.bucket_policy import set_bucket_policy
from cloud_guardian.utils.loaders import (
    extract_bucket_names,
    load_iam_data_into_dictionaries,
)
from cloud_guardian.utils.maps import BiMap
from cloud_guardian.utils.strings import get_name_from_arn


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
            user_info = create_user_and_access_keys(self.iam, user_name)
            user_arn = user_info["Arn"]
            self.credentials[user_arn] = (
                user_info["AccessKeyId"],
                user_info["SecretAccessKey"],
            )
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
