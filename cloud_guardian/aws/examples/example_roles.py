import json

import boto3
from moto import mock_aws


@mock_aws
def main():
    # Initialize the IAM client
    iam = boto3.client("iam")

    # Trust relationship policy JSON for an AWS service
    trust_relationship = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    # Create a new IAM role
    try:
        role_name = "ExampleRole"
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_relationship),
            Description="An example IAM role.",
        )
        role_arn = response["Role"]["Arn"]
        print(f"Created IAM Role ARN: {role_arn}")
    except Exception as e:
        print(f"Failed to create role: {e}")

    # Here you would normally have the policy ARN, but for `moto`, create it manually
    try:
        # Create a dummy policy to simulate the managed policy (if needed)
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": "s3:ReadOnly", "Resource": "*"}
            ],
        }
        policy_response = iam.create_policy(
            PolicyName="AmazonS3ReadOnlyAccess",
            PolicyDocument=json.dumps(policy_document),
        )
        policy_arn = policy_response["Policy"]["Arn"]

        # Attach the policy to the role
        response = iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
        print(f"Policy {policy_arn} attached to role {role_name} successfully.")
    except Exception as e:
        print(f"Failed to attach policy: {e}")

    # Trust relationship policy JSON for specific IAM users
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": [
                        "arn:aws:iam::123456789012:user/User1",
                        "arn:aws:iam::123456789012:user/User2",
                    ]
                },
                "Action": "sts:AssumeRole",
            }
        ],
    }

    role_name = "ExampleRole"

    # Update the trust relationship for the role
    try:
        response = iam.update_assume_role_policy(
            RoleName=role_name, PolicyDocument=json.dumps(trust_policy)
        )
        print(f"Trust policy updated successfully for role {role_name}.")
    except Exception as e:
        print(f"Failed to update trust policy: {e}")


main()
