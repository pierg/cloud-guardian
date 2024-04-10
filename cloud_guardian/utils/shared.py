from pathlib import Path

repo_path = Path(__file__).parent.parent.parent

data_path = repo_path / "data"

output_path = repo_path / "output"

constraints_path = data_path / "constraints.json"
