

def get_concrete_identities(identities_dict):
    """Extract identities that have no includes."""
    return [identity for identity in identities_dict.values() if len(identity.includes) == 0]
