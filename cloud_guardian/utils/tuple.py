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