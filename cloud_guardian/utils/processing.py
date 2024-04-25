import json
import os

from cloud_guardian.utils.shared import data_path


def process_json_data(data):
    if isinstance(data, dict):
        keys_to_remove = [
            "UserName",
            "GroupName",
            "RoleName",
            "PolicyName",
            "CreateDate",
        ]
        for key in list(data.keys()):
            if key in keys_to_remove:
                del data[key]
            elif isinstance(data[key], str) and "arn:" in data[key]:
                data["ID"] = data.pop(key)
            else:
                process_json_data(data[key])
    elif isinstance(data, list):
        for item in data:
            process_json_data(item)


def process_files(input_dir, output_dir):
    # Create the processed folder if it does not exist
    os.makedirs(output_dir, exist_ok=True)

    # List all JSON files in the original directory
    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            input_file_path = os.path.join(input_dir, filename)
            output_file_path = os.path.join(output_dir, filename)

            # Open and read the JSON data
            with open(input_file_path, "r") as file:
                print(f"Processing {input_file_path}")
                json_data = json.load(file)

            # Process the JSON data
            process_json_data(json_data)

            # Write the processed data to the output directory
            with open(output_file_path, "w") as file:
                json.dump(json_data, file, indent=4)


if __name__ == "__main__":
    input_directory = data_path / "toy_example" / "original"
    output_directory = data_path / "toy_example" / "processed"
    process_files(input_directory, output_directory)
