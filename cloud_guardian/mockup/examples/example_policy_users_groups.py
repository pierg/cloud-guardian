import boto3
import json
from moto import mock_aws

# Example that show how to:
#       Create policies, users, groups
#       Assing policies to users and groups
#       Assign users to groups

# Start the mock for IAM
@mock_aws
def main():
    # Initialize the IAM client
    iam = boto3.client('iam')

    # Define the policy
    policy = {
        'PolicyName': 'ExamplePolicy',
        'PolicyDocument': {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "s3:ListAllMyBuckets",
                    "Resource": "arn:aws:s3:::*"
                }
            ]
        },
        'Description': 'Policy for ExamplePolicy'
    }

    # Create the policy
    try:
        response = iam.create_policy(
            PolicyName=policy['PolicyName'],
            PolicyDocument=json.dumps(policy['PolicyDocument']),
            Description=policy['Description'],
            Path='/'
        )
        # Retrieve the ARN of the newly created policy
        policy_arn = response['Policy']['Arn']
        print(f"Created policy ARN: {policy_arn}")
    except Exception as e:
        print(f"Failed to create policy: {e}")

    # Create a new IAM user
    try:
        user_name = 'ExampleUser'
        response = iam.create_user(UserName=user_name)
        user_arn = response['User']['Arn']
        print(f"Created IAM User ARN: {user_arn}")
    except Exception as e:
        print(f"Failed to create user: {e}")

    # Create a new IAM group
    try:
        group_name = 'ExampleGroup'
        response = iam.create_group(GroupName=group_name)
        group_arn = response['Group']['Arn']
        print(f"Created IAM Group ARN: {group_arn}")
    except Exception as e:
        print(f"Failed to create group: {e}")

    # Attach the policy to the user
    try:
        response = iam.attach_user_policy(
            UserName=user_name,
            PolicyArn=policy_arn
        )
        print(f"Policy {policy_arn} attached to user {user_name} successfully.")
    except Exception as e:
        print(f"Failed to attach policy to user: {e}")

    # Attach the policy to the group
    try:
        response = iam.attach_group_policy(
            GroupName=group_name,
            PolicyArn=policy_arn
        )
        print(f"Policy {policy_arn} attached to group {group_name} successfully.")
    except Exception as e:
        print(f"Failed to attach policy to group: {e}")

    # Add user to the group
    try:
        response = iam.add_user_to_group(
            GroupName=group_name,
            UserName=user_name
        )
        print(f"User {user_name} added to group {group_name} successfully.")
    except Exception as e:
        print(f"Failed to add user to group: {e}")

# Run the main function to execute all operations under the mock
main()


