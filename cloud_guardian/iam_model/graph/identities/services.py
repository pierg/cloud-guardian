from dataclasses import dataclass


@dataclass(frozen=True)
class SupportedService:
    service_principal: str
    description: str

    def __str__(self):
        return f"{self.service_principal} - {self.description}"


@dataclass(frozen=True)
class EC2Service(SupportedService):
    service_principal: str = "ec2.amazonaws.com"
    description: str = "Allows EC2 instances to interact with specified AWS resources."


@dataclass(frozen=True)
class LambdaService(SupportedService):
    service_principal: str = "lambda.amazonaws.com"
    description: str = (
        "Allows Lambda functions to access AWS services under given permissions."
    )


@dataclass(frozen=True)
class ECS_TasksService(SupportedService):
    service_principal: str = "ecs-tasks.amazonaws.com"
    description: str = (
        "Allows ECS tasks to assume roles for accessing other AWS services."
    )


@dataclass(frozen=True)
class S3Service(SupportedService):
    service_principal: str = "s3.amazonaws.com"
    description: str = (
        "Service role for Amazon S3 to perform actions on behalf of the user."
    )


class ServiceFactory:
    _instances = {}
    _service_types = {
        EC2Service.service_principal: EC2Service,
        LambdaService.service_principal: LambdaService,
        ECS_TasksService.service_principal: ECS_TasksService,
        S3Service.service_principal: S3Service,
    }

    @classmethod
    def get_or_create(cls, service_principal: str):
        if service_principal not in cls._instances:
            if service_principal in cls._service_types:
                service_class = cls._service_types[service_principal]
                cls._instances[service_principal] = service_class()
            else:
                raise ValueError(f"Service '{service_principal}' is not supported.")
        return cls._instances[service_principal]


# json_data = {
#   "Roles": [
#     {
#       "RoleName": "EC2Role",
#       "RoleId": "ARIDEXAMPLE1234",
#       "Arn": "arn:aws:iam::123456789012:role/EC2Role",
#       "CreateDate": "2020-01-03T12:00:00Z",
#       "AssumeRolePolicyDocument": {
#         "Version": "2012-10-17",
#         "Statement": [
#           {
#             "Effect": "Allow",
#             "Principal": {
#               "Service": "ec2.amazonaws.com",
#               "AWS": "arn:aws:iam::123456789012:user/Alice"
#             },
#             "Action": "sts:AssumeRole"
#           }
#         ]
#       }
#     },
#     {
#       "RoleName": "LambdaExecutionRole",
#       "RoleId": "ARIDEXAMPLE5678",
#       "Arn": "arn:aws:iam::123456789012:role/LambdaExecutionRole",
#       "CreateDate": "2020-02-03T12:00:00Z",
#       "AssumeRolePolicyDocument": {
#         "Version": "2012-10-17",
#         "Statement": [
#           {
#             "Effect": "Allow",
#             "Principal": {
#               "Service": "lambda.amazonaws.com",
#               "Federated": "cognito-identity.amazonaws.com",
#               "AWS": "arn:aws:iam::123456789012:root"
#             },
#             "Action": "sts:AssumeRole"
#           }
#         ]
#       }
#     }
#   ]
# }

# for role_data in json_data["Roles"]:
#     for statement in role_data["AssumeRolePolicyDocument"]["Statement"]:
#         if "Service" in statement["Principal"]:
#             service_principal = statement["Principal"]["Service"]
#             service = ServiceFactory.get_or_create(service_principal)
#             print(service)
