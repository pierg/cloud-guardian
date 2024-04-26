from dataclasses import dataclass


@dataclass(frozen=True)
class SupportedService:
    service_principal: str
    description: str

    def __str__(self):
        return f"{self.service_principal} - {self.description}"

    @property
    def id(self):
        return self.service_principal


@dataclass(frozen=True)
class EC2Service(SupportedService):
    name: str = "EC2"
    service_principal: str = "ec2.amazonaws.com"
    description: str = "Allows EC2 instances to interact with specified AWS resources."


@dataclass(frozen=True)
class LambdaService(SupportedService):
    name: str = "Lambda"
    service_principal: str = "lambda.amazonaws.com"
    description: str = (
        "Allows Lambda functions to access AWS services under given permissions."
    )


@dataclass(frozen=True)
class ECS_TasksService(SupportedService):
    name: str = "ECS Tasks"
    service_principal: str = "ecs-tasks.amazonaws.com"
    description: str = (
        "Allows ECS tasks to assume roles for accessing other AWS services."
    )


@dataclass(frozen=True)
class S3Service(SupportedService):
    name: str = "S3"
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
