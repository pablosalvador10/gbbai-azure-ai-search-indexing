1. [Development Workflow Introduction](#development-workflow-introduction)
2. [Development Process](#development-process)
   - [Starting Development](#starting-development)
   - [Optional Steps](#optional-steps)
   - [Developing New Features or Fixing Bugs](#developing-new-features-or-fixing-bugs)
   - [Pull Requests](#pull-requests)
   - [Issues](#issues)
   - [Understanding Version Numbering](#understanding-version-numbering)
   - [Branching Strategy Visualized](#branching-strategy-visualized)
3. [Development Best Practices](#development-best-practices)
   - [Benefits of Committing to Testing Early](#benefits-of-committing-to-testing-early)
   - [Development Trick 1: Using Jupyter Notebooks and %%ipytest](#development-trick-1-using-jupyter-notebooks-and-ipytest)


## Development Workflow Introduction

Adhering to the outlined development steps is essential for fostering effective collaboration, ensuring engineering excellence, and maintaining a product-focused mindset within the team:

- **Clear Communication**: These clear, structured steps minimize misunderstandings, promoting a collaborative environment.

- **Code Quality**: By following prescribed tests, documentation, and hooks, we ensure our code is clean, maintainable, and consistent.

- **Product Focus**: A disciplined workflow helps the team concentrate on delivering valuable features and addressing crucial issues, enhancing the end product.

- **Efficient Collaboration**: With streamlined branching and merging, team members can seamlessly integrate their contributions without disrupting others’ work.

Through these guidelines, team members can collaboratively build a robust, user-centered software product while upholding high technical and product standards.

## Development Process 🚀
### Starting Development

1. **Initiate a New Issue**: Begin by opening a new issue—whether it's a bug or a feature—on the repository's issue tracker or on Jira.

2. **Clone the Repository**:
    ```shell
    git clone https://github.example.com/{your_project}.git
    ```

3. **Set Up Development Environment**:
    First, fill out the `environment.yaml` file with the following content:

    ```yaml
    name: my-template-environment
    channels:
      - conda-forge
      - defaults
    dependencies:
      - python=3.10
      - pip
      - pip:
        - -r file:requirements.txt
        - -r file:requirements-codequality.txt
        - -r file:requirements-pipelines.txt
    ```

    Second, take the following steps with regard to the requirement files:

    + `requirements.txt`: This file should list all packages that are essential for executing your code located in the src directory. Please meticulously check and make sure every package that your code depends on is listed with the appropriate version number.

    + `requirements-codequality.txt` : Populate this file with packages necessary for conducting code quality checks and supporting continuous integration and continuous delivery (CI/CD) execution. These packages are not directly involved in running your main code but are crucial for maintaining code quality and facilitating the CI/CD process. Ensure to include packages that help in linting, formatting, and any other code quality assurance processes that you utilize.

    + `requirements-pipelines.txt` : This file is pivotal for orchestration purposes. It should contain packages that are essential for automating the execution of your code in a pipeline format. In other words, any package that supports the automated, sequential execution of your code from development to deployment should be listed in this file.

    > Additionally, during the development phase, as you integrate new packages into your project, it's imperative to promptly add these to the respective requirement files.

    After saving the `environment.yaml` file, create your Conda environment based on the YAML file:

    ```bash
    conda env create -f environment.yaml
    conda activate my-template-environment
    ```

   This process initializes your development environment with the specified Python version and installs the necessary packages listed in the respective requirements files.

### Optional Steps

- **Integrate with VSCode (Optional)**:
    - Install the `Python` and `Jupyter keymap` extensions for Visual Studio Code.
    - Ensure you have `ipykernel` installed and activated within the `your_environment` environment:
        ```bash
        conda activate your_environment
        conda install ipykernel
        ```
    - You should be able to see the environment listed as a kernel option within VSCode.

5. **Setup Hooks for Code Quality Assurance**:

    ```bash
    make set_up_precommit_and_prepush CONDA_ENV=my-template-environment
    ```
    - This sets up various hooks to ensure code quality, including `flake8`, `mypy`, `isort`, `black`, `check-yaml`, `end-of-file-fixer`, and `trailing-whitespace`.

### Developing New Features or Fixing Bugs

6. Branch off from `staging` for new features or bug fixes:
    ```git
    git checkout -b feature/YourFeatureName_or_BugFix
    ```

7. Incorporate tests and update documentation as necessary.

8. Run test suite and style checks to ensure integrity:
    ```bash
    make run_code_quality_checks
    make run_tests
    ```

9. Update `requirements` as necessary and document any changes in your Pull Request (PR) and `CHANGELOG`.

10. Commit and push your changes:
    ```git
    git commit -m 'TypeOfChange/YourChangeDescription'
    git push origin YourBranchName
    ```

### Pull Requests

- Open a PR targeting either `staging` or `main`. Fill in the PR template with clear and detailed instructions.
- Upon submission, a github CI/CD pipeline will trigger automatically.

### Issues

- For bug tracking and feature requests, use GitHub issues. Be clear and detailed in your description to facilitate reproduction and resolution of the issue.

### Understanding Version Numbering

- **Major Releases (e.g., 5.0.0)**: Include breaking changes, not backward-compatible with previous versions.
- **Minor Releases (e.g., 5.1.0)**: Introduce new features while maintaining backward compatibility.
- **Patch Releases (e.g., 5.1.4)**: Minor fixes or security patches, always backward-compatible.

### Branching Strategy Visualized

![Branching Strategy Diagram](utils/images/flow.png)

**Explanation**:
- `feature/new_feature branch` is for development.
- `staging branch` is for the staging environment, where code is further tested and validated.
- `main branch` is the production environment with the

### Development Best Practices

Fast Development is a high-paced iterative cycle between development and testing during the early stages of ML/software development. In this phase, developers identify bugs, issues, and defects without relying heavily on automated tools. It's essential during the rapid experimentation and prototyping phase of the ML lifecycle.

### Benefits of Committing to Testing Early

Committing to testing early in the development process, even during fast, iterative cycles, offers several advantages:
- Quick identification and resolution of bugs and defects.
- Improved code reliability and maintainability.
- Enhanced understanding of the code's behavior and performance.

### Development Trick 1.: Using Jupyter Notebooks and %%ipytest
For rapid development and testing, Jupyter Notebooks offer a convenient and interactive environment. Here’s a practical trick for fast development using Jupyter Notebooks:

1. Write your function within a Jupyter Notebook cell.
2. Use the `%%ipytest` magic command to quickly test the function within the notebook environment.

Suppose you are developing a function `add_numbers`:

```python
def add_numbers(a, b):
    """
    This function adds two numbers.

    Parameters:
    a (int or float): The first number.
    b (int or float): The second number.

    Returns:
    int or float: The sum of a and b.
    """
    return a + b
```
You can quickly test this function using %%ipytest within a Jupyter Notebook cell:

```python

%%ipytest
def test_add_numbers():
    assert add_numbers(1, 2) == 3
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0
```

> %%ipytest is a cell magic command in Jupyter that allows for running tests in isolation and displaying the results inline, offering immediate feedback. This approach is valuable when building functions incrementally, as it allows for immediate testing and validation. It's particularly useful for testing data transformations and algorithms during the early stages of development.
