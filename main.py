from cloud_guardian import logger
from cloud_guardian.aws.aws_manager import AWSManager
from cloud_guardian.utils.processing import process_files
from cloud_guardian.utils.shared import data_path
from moto import mock_aws

mock = mock_aws()
mock.start()

data_folder = data_path / "toy_example"
process_files(data_folder / "original", data_folder / "processed")

aws_manager = AWSManager()

aws_manager.import_from_json(data_folder / "processed")


mock.stop()