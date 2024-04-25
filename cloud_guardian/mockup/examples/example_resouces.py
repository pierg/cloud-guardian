import json

import boto3
from moto import mock_aws


@mock_aws
def main():
    # Initialize the S3 client
    s3 = boto3.client("s3", region_name="us-east-1")

    # Bucket name
    bucket_name = "example-bucket"

    # Create an S3 bucket
    try:
        s3.create_bucket(Bucket=bucket_name)
        print(f"Created bucket {bucket_name} successfully.")
    except Exception as e:
        print(f"Failed to create bucket: {e}")

    # Upload an object to the bucket
    try:
        object_name = "example-file.txt"
        s3.put_object(Bucket=bucket_name, Key=object_name, Body="Sample content")
        print(f"Uploaded {object_name} to {bucket_name} successfully.")
    except Exception as e:
        print(f"Failed to upload object: {e}")

    # Define a bucket policy
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*",
            }
        ],
    }

    # Set the bucket policy
    try:
        policy_string = json.dumps(bucket_policy)
        s3.put_bucket_policy(Bucket=bucket_name, Policy=policy_string)
        print(f"Policy set successfully on bucket {bucket_name}.")
    except Exception as e:
        print(f"Failed to set bucket policy: {e}")


# Run the main function to execute all operations under the mock
main()
