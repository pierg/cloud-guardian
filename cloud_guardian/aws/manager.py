from pathlib import Path

import boto3
from botocore.credentials import ReadOnlyCredentials
from cloud_guardian import logger
from cloud_guardian.aws.importer import JsonImporter


class AWSManager:
    def __init__(self, region_name="us-east-1"):
        self.region_name = region_name
        self.session = boto3.Session(region_name=self.region_name)
        self.credentials = {}  # Stores credentials indexed by ARN or 'default'
        self.store_credentials(
            "default", self.session.get_credentials().get_frozen_credentials()
        )
        self.refresh_clients()
        self.importer = JsonImporter()

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

    def import_data(self, folder_path: Path):
        self.importer.import_data(folder_path, self)
