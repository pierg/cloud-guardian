# TODO: improve to extract more information from the ARN
def extract_policy_from_ARN(arn: str) -> str:
    """
    Extracts the policy part from the ARN format 'arn:aws:iam::aws:policy/{{policy}}'.
    """
    policy = arn.split("/")[-1]
    return policy
