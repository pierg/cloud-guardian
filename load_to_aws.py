import json

import boto3
from cloud_guardian.iam_static.graph.permission.permission import PermissionFactory
from cloud_guardian.mockup.helpers_iam import (
    add_user_to_group,
    attach_policy_to_group,
    attach_policy_to_user,
    create_group,
    create_policy,
    create_role,
    create_user,
    get_principals_for_role,
)
from cloud_guardian.mockup.helpers_s3 import *
from cloud_guardian.utils.loaders import (
    extract_bucket_names,
    load_iam_data_into_dictionaries,
)
from cloud_guardian.utils.processing import process_files
from cloud_guardian.utils.shared import data_path
from cloud_guardian.utils.strings import get_name_and_type_from_id
from loguru import logger
from moto import mock_aws

data_folder = data_path / "toy_example"

process_files(data_folder / "original", data_folder / "processed")


groups_dict, policies_dict, roles_dict, users_dict = load_iam_data_into_dictionaries(
    data_folder / "processed"
)


mock = mock_aws()
mock.start()


iam = boto3.client("iam")
s3 = boto3.client("s3", region_name="us-east-1")



bi_map = BiMap()


# Create identity-based policies and attach them to the identities
for policy in policies_dict["IdentityBasedPolicies"]:
    policy_name = get_name_and_type_from_id(policy["ID"])
    policy_arn = create_policy(iam, policy_name, policy["PolicyDocument"])
    bi_map.add(policy_arn, policy["ID"])


# Create groups and attach policies
for group in groups_dict["Groups"]:
    group_name = get_name_and_type_from_id(group["ID"])
    group_arn = create_group(iam, group_name)
    bi_map.add(group_arn, group["ID"])
    for policy in group["AttachedPolicies"]:
        policy_arn = bi_map.get(policy["ID"])
        attach_policy_to_group(iam, policy_arn, group_name)


# Create users, attach policies
for user in users_dict["Users"]:
    user_name = get_name_and_type_from_id(user["ID"])
    user_arn = create_user(iam, user_name)
    bi_map.add(user_arn, user["ID"])
    for policy in user.get("AttachedPolicies", []):
        policy_arn = bi_map.get(policy["ID"])
        attach_policy_to_user(iam, policy_arn, user_name)


# Add users to groups
for group in groups_dict["Groups"]:
    group_name = get_name_and_type_from_id(group["ID"])
    for user in group["Users"]:
        user_name = get_name_and_type_from_id(bi_map.get(user["ID"]))
        add_user_to_group(iam, user_name, group_name)


# Create roles and attach policies
for role in roles_dict["Roles"]:
    role_name = get_name_and_type_from_id(role["ID"])
    role_arn = create_role(iam, role_name, role["AssumeRolePolicyDocument"])
    bi_map.add(role_arn, role["ID"])


# # Process resource-based policies
for policy in policies_dict["ResourceBasedPolicies"]:
    for resource_name in extract_bucket_names(policy):
        create_bucket(s3, resource_name)
        set_bucket_policy(s3, resource_name, policy["PolicyDocument"])


# After loading into aws with boto3 we can pull and build our graph data strucutre

# E.g.
#     policy_document = get_policy_document(iam, policy_arn)
#     permissions = PermissionFactory.from_policy_document(policy_document)

principals = get_principals_for_role(iam, role_name)
print(f"Role {role_name} can be assumed by: {principals}")


mock.stop()

print("Setup completed.")
