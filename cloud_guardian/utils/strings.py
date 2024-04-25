def get_name_from_arn(arn: str) -> str:
    """Gets only the name from an ARN."""
    return arn.split("/")[-1]
