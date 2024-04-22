# TODO: improve to extract more information from the ARN
def extract_identifier_from_ARN(arn: str) -> str:
    """
    Extracts the 'identifier' from the ARN format 'arn:aws:iam::aws:{{ressource, policy}}/{{identifier}}'.
    """
    policy = arn.split("/")[-1]
    return policy
