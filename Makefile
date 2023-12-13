PYTHON_INTERPRETER = python3
CONDA_ENV ?= my-template-environment
export PYTHONPATH=$(PWD):$PYTHONPATH;

# Target for setting up pre-commit and pre-push hooks
set_up_precommit_and_prepush:
	pre-commit install -t pre-commit
	pre-commit install -t pre-push

# The 'check_code_quality' command runs a series of checks to ensure the quality of your code.
check_code_quality:
	# Running 'ruff' to automatically fix common Python code quality issues.
	@pre-commit run ruff --all-files

	# Running 'black' to ensure consistent code formatting.
	@pre-commit run black --all-files

	# Running 'isort' to sort and organize your imports.
	@pre-commit run isort --all-files

	# # Running 'flake8' for linting.
	@pre-commit run flake8 --all-files

	# Running 'mypy' for static type checking.
	@pre-commit run mypy --all-files

	# Running 'check-yaml' to validate YAML files.
	@pre-commit run check-yaml --all-files

	# Running 'end-of-file-fixer' to ensure files end with a newline.
	@pre-commit run end-of-file-fixer --all-files

	# Running 'trailing-whitespace' to remove unnecessary whitespaces.
	@pre-commit run trailing-whitespace --all-files

	# Running 'interrogate' to check docstring coverage in your Python code.
	@pre-commit run interrogate --all-files

	# Running 'bandit' to identify common security issues in your Python code.
	bandit -c pyproject.toml -r .

fix_code_quality:
	# Automatic fixes for code quality (not doing in production only dev cycles)
	black .
	isort .
	ruff --fix .

# Targets for running tests
run_unit_tests:
	$(PYTHON_INTERPRETER) -m pytest --cov=my_module --cov-report=term-missing --cov-config=.coveragerc

check_and_fix_code_quality: fix_code_quality check_code_quality
check_and_fix_test_quality: run_unit_tests

# Targets for various operations and tests

# Colored text
RED = \033[0;31m
NC = \033[0m # No Color
GREEN = \033[0;32m

# Helper function to print section titles
define log_section
	@printf "\n${GREEN}--> $(1)${NC}\n\n"
endef

INPUT_PATH= "/Users/salv91/Desktop/open-source/ml-project-template/utils/data/BankChurners.csv"
OUTPUT_DIRECTORY= "/Users/salv91/Desktop/open-source/ml-project-template/notebooks/dev/test"

## run with Omegaconf + Click

test_fe_passing_args:
	$(call log_section,Running feature engineering with specified arguments)
	$(PYTHON_INTERPRETER) $(PWD)/pipelines/feature_engineering/components.py run-feature-engineering --input_path $(INPUT_PATH) --output_directory $(OUTPUT_DIRECTORY)

test_fe_no_passing_args:
	$(call log_section,Running feature engineering with default arguments)
	$(PYTHON_INTERPRETER) $(PWD)/pipelines/feature_engineering/components.py run-feature-engineering

test_training_data_prep_args:
	$(call log_section,Preparing training data with specified estimator and sampling techniques)
	$(PYTHON_INTERPRETER) $(PWD)/pipelines/training/components.py run-training-data-prep --estimator "AdaBoostClassifier" --perform-sampling-techniques "upsampling"

test_training:
	$(call log_section,Training model with specified estimator)
	$(PYTHON_INTERPRETER) $(PWD)/pipelines/training/components.py run-training --estimator "AdaBoost_upsampling"

# Target for running refitting with Hydra
test_reffiting_hydra:
	$(call log_section,Running model refitting using Hydra with specified date)
	$(PYTHON_INTERPRETER) $(PWD)/pipelines/training/components_hydra.py pipeline_settings.date="'14_10_2023'"

test_reffiting_hydra_multirun:
	$(call log_section,Running model refitting using Hydra with specified date)
	$(PYTHON_INTERPRETER) $(PWD)/pipelines/training/components_hydra.py --multirun pipeline_settings.date="'14_10_2023'","'14_12_2023'"


run_pylint:
	@echo "Running linter"
	find . -type f -name "*.py" ! -path "./tests/*" | xargs pylint -disable=logging-fstring-interpolation > utils/pylint_report/pylint_report.txt
