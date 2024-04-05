<p align="center">
  <!-- <img src="https://raw.githubusercontent.com/PKief/vscode-material-icon-theme/ec559a9f6bfd399b82bb44393651661b08aaf7ba/icons/folder-markdown-open.svg" width="100" alt="project-logo"-->
</p>
<p align="center">
    <h1 align="center">cloud guardian</h1>
</p>
<p align="center">
	<img src="https://img.shields.io/github/license/pierg/cloud-guardian?style=default&logo=opensourceinitiative&logoColor=white&color=0080ff" alt="license">
	<img src="https://img.shields.io/github/last-commit/pierg/cloud-guardian?style=default&logo=git&logoColor=white&color=0080ff" alt="last-commit">
	<img src="https://img.shields.io/github/languages/top/pierg/cloud-guardian?style=default&color=0080ff" alt="repo-top-language">
	<img src="https://img.shields.io/github/languages/count/pierg/cloud-guardian?style=default&color=0080ff" alt="repo-language-count">
<p>
<p align="center">
	<!-- default option, no dependency badges. -->
</p>


##  Overview

Cloud Guardian models and analyze IAM policies. 


---


##  Getting Started

**System Requirements:**

* **Python**: `version 3.11`
* **[*Poetry*](https://python-poetry.org/docs/)** 

###  Installation

1. Clone the cloud-guardian repository:

```console
$ git clone https://github.com/pierg/cloud-guardian
```

2. Change to the project directory:
```console
$ cd cloud-guardian
```

3. Install the dependencies:
```console
$ poetry install
```

###  Usage

Run cloud-guardian using the command below:
```console
$ python main.py
```


---

##  Repository Structure

```sh
└── cloud-guardian/
    ├── Makefile
    ├── README.md
    ├── cloud_guardian
    │   ├── __init__.py
    │   ├── ex_conditions.py
    │   ├── iam_model
    │   ├── main.py
    │   └── utils
    ├── data
    │   ├── fake_data_large.csv
    │   ├── fake_data_larger.csv
    │   └── fake_data_small.csv
    ├── output
    │   ├── iam_graph_large.pdf
    │   ├── iam_graph_larger.pdf
    │   └── iam_graph_small.pdf
    └── pyproject.toml
```