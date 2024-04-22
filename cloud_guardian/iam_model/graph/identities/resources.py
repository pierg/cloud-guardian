from dataclasses import dataclass


@dataclass
class Resource:
    name: str
    arn: str
    service: str
    resource_type: str

    def __hash__(self):
        return hash((self.name, self.arn, self.service, self.resource_type))

    def __eq__(self, other):
        if not isinstance(other, Resource):
            return False
        return (
            self.name,
            self.arn,
            self.service,
            self.resource_type,
        ) == (
            other.name,
            other.arn,
            other.service,
            other.resource_type,
        )

    def __str__(self):
        return (
            f"Resource Name: {self.name}, ARN: {self.arn}, "
            f"Service: {self.service}, Resource Type: {self.resource_type}\n"
        )

    @property
    def id(self):
        return self.arn


class ResourceFactory:
    _instances = {}

    @classmethod
    def get_or_create(cls, name, arn, service, resource_type):
        if arn not in cls._instances:
            cls._instances[arn] = Resource(
                name=name,
                arn=arn,
                service=service,
                resource_type=resource_type,
            )
        return cls._instances[arn]

    @classmethod
    def from_dict(cls, resource_dict):
        name = resource_dict["ResourceName"]
        arn = resource_dict["ResourceArn"]
        service = resource_dict["Service"]
        resource_type = resource_dict["ResourceType"]
        return cls.get_or_create(name, arn, service, resource_type)
