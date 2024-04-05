# Define a sample resource
from cloud_guardian.iam_model.identities import Resource
from cloud_guardian.iam_model.permission import Condition, Effect, IAMAction, Permission

# Example on how to define and check permissions with conditions

sample_resource = Resource(id="resource-1", type="Document")

permission = Permission(
    id="perm-1",
    effect=Effect.ALLOW,
    action=IAMAction.READ,
    resource=sample_resource,
    conditions=[
        Condition("requester_ip", "in_range", "192.168.1.0/24"),
        Condition("request_time", "time_between", ("09:00", "17:00")),
    ],
)

# Define a context matching the conditions
context = {"requester_ip": "192.168.1.105", "request_time": "14:30"}

# Check if the permission is granted based on the context
is_allowed = permission.is_granted(context)
print(f"Permission granted: {is_allowed}")
