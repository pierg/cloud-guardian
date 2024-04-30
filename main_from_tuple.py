from cloud_guardian import logger
from cloud_guardian.aws.manager import AWSManager
from cloud_guardian.iam_dynamic.model import IAMGraphMDP
from cloud_guardian.iam_static.model import IAMManager
from cloud_guardian.utils.processing import process_files
from cloud_guardian.utils.shared import data_path
from moto import mock_aws

mock = mock_aws()
mock.start()

data_folder = data_path / "toy_example"
process_files(data_folder / "original", data_folder / "processed")

aws_manager = AWSManager()

aws_manager.import_from_json(data_folder / "generated")

iam_manager = IAMManager(aws_manager)

iam_manager.update_graph()

dynamic_model = IAMGraphMDP(iam_manager, aws_manager)

# # Perform Privilege Escalation Attack
# # Step 1 - Eve assumerole of SuperUser
# trace_1 = {
#     "entity": "Eve",
#     "action": "sts:AssumeRole",
#     "parameters": {"role_arn": "arn:aws:iam::123456789012:role/SuperUserRole"},
# }
# dynamic_model.step_from_dict(trace_1)

# # Step 2 - Eve creates a new user
# trace_2 = {
#     "entity": "Eve",
#     "action": "iam:CreateUser",
#     "parameters": {"user_name": "NewUser"},
# }
# dynamic_model.step_from_dict(trace_2)

# # Step 3 - Eve creates a new policy
# trace_3 = {
#     "entity": "Eve",
#     "action": "iam:CreatePolicy",
#     "parameters": {
#         "policy_name": "AdminPolicy",
#         "actions": ["s3:*"],
#         "resource": "*",
#     },
# }
# dynamic_model.step_from_dict(trace_3)

# # Step 4 - Eve attaches the admin policy to the new user
# trace_4 = {
#     "entity": "Eve",
#     "action": "iam:AttachUserPolicy",
#     "parameters": {
#         "user_name": "NewUser",
#         "policy_name": "AdminPolicy",
#     },
# }
# dynamic_model.step_from_dict(trace_4)

mock.stop()
