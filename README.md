# Azure AI services Quick Start Accelerator <img src="./utils/images/azure_logo.png" alt="Azure Logo" style="width:30px;height:30px;"/>
Welcome to the Azure AI Quick Start Accelerator! This repository is designed as a rapid launchpad for your complex AI systems projects, harnessing the power of Azure AI services. Tailored for both enterprise and academic environments, this accelerator integrates best practices to ensure a seamless development journey from start to finish.



## 🌟 Goal
The primary goal of this Accelerator is to provide a quick start for developing and deploying complex AI solutions using Azure AI services. It acts as a comprehensive guide for both novices and seasoned professionals, enabling the efficient establishment, deployment, and management of sophisticated AI systems.

## 💼 Contributing: Your Gateway to Advanced AI Development & Collaboration!

Eager to make significant contributions? Our **[CONTRIBUTING](./CONTRIBUTING.md)** guide is your essential resource! It lays out a clear path for:

- **🔄 Development Workflow**: Familiarize yourself with our optimized workflow, designed to foster effective collaboration and a focus on product-centric development.

- **🚀 Advanced AI Development Process**: Dive into the specifics of managing complex AI projects, from issue reporting to pull requests, all while adhering to best practices in advanced feature development and complex system troubleshooting.

- **🔍 Testing & QA for AI Systems**: Explore the importance of rigorous testing in AI projects and discover efficient development and testing techniques tailored for AI systems with tools like Jupyter Notebooks and `%%ipytest`.

- **🔢 Version & Branching Strategies for AI Projects**: Understand our versioning system and explore the project’s branching strategy, which ensures smooth transitions between development, staging, and production, especially for AI-driven applications.

- To stay updated with the latest developments and document significant changes to this project, please refer to [CHANGELOG.md](CHANGELOG.md).



## 🌲 Project Tree Structure

```
📂 ml-project-template
┣ 📂 docs <- Documentation for the project. README
┣ 📂 notebooks <- For development, EDA, and quick testing (Jupyter notebooks for analysis and development). README
┣ 📂 pipelines <- Orchestrates with Azure Pipeline/Airflow for ML workflows. More in README.
┣ 📦 src <- Houses main source code for data processing, feature engineering, modeling, inference, and evaluation. README
┣ 📂 test <- Runs unit and integration tests for code validation and QA. Check README.
┣ 📂 utils <- Contains utility functions and shared code used throughout the project. Detailed info in README
┣ 📜 .pre-commit-config.yaml <- Config for pre-commit hooks ensuring code quality and consistency.
┣ 📜 CHANGELOG.md <- Logs project changes, updates, and version history.
┣ 📜 CONTRIBUTING.md <- Guidelines for contributing to the project.
┣ 📜 environment.yaml <- Conda environment configuration.
┣ 📜 Makefile <- Simplifies common development tasks and commands.
┣ 📜 pyproject.toml <- Configuration file for build system requirements and packaging-related metadata.
┣ 📜 README.md <- Overview, setup instructions, and usage details of the project.
┣ 📜 requirements-codequality.txt <- Requirements for code quality tools and libraries.
┣ 📜 requirements-pipelines.txt <- Requirements for pipeline-related dependencies.
┣ 📜 requirements.txt <- General project dependencies.
```

##  👨🏽‍💻 System Design and Architecture

## CI/CD
