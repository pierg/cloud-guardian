from cloud_guardian.utils.shared import data_path
import joblib
import matplotlib.pyplot as plt
import pandas as pd




data_file = data_path / "sensitive" / "ds_4_tuples.joblib"

data = joblib.load(data_file)


# Assuming the data is in a format that can be directly converted to a DataFrame
df = pd.DataFrame(data)

# Print the first 50 rows of the DataFrame
print(df.head(50))


# Assuming 'permission' is one of the columns in the DataFrame
# Get unique entries in the 'permission' column
unique_permissions = pd.unique(df['permission'])

# Convert the array of unique permissions to a set
permissions_set = set(unique_permissions)

# Print the set of unique permissions
print("\n".join(permissions_set))


# TODO: Create the json structure as in "toy/example/processed
# you can use source and destination columns as ids, 
# permission FULL_CONTROL = * action
# permission belongs => relates users to groups
# permission sts:AssumeRole => relates roles 
# etc..
# you can use a custom utils/strings/get_name_and_type_from_id function to parse the source and destination
# and get the type (role, group etc..) and an id (e.g. identity_1) etc..

def create_jsons_from_tuple(data, output_folder):
    """Create the json structure as in "toy/example/processed"""