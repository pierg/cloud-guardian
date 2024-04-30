import joblib
import pandas as pd
from cloud_guardian.utils.shared import data_path

data_file = data_path / "sensitive" / "data.joblib"

data = joblib.load(data_file)

# Assuming the data is in a format that can be directly converted to a DataFrame
df = pd.DataFrame(data)


# Print all types of strings for each column and save to files in the output directory
def save_all_types(df: pd.DataFrame, output_directory: str):
    for column in df.columns:
        types = df[column].unique()
        with open(f"{output_directory}/{column}.txt", "w") as file:
            for t in types:
                file.write(f"{t}\n")


save_all_types(df, data_path / "sensitive")
