def generate_arn(resource_type: str, resource_name: str) -> str:
    """Simulates generating an ARN for an identity or resource."""
    return f"arn:aws:{resource_type}::123456789012:{resource_name}"
