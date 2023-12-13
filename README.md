# Langchain & Azure AI Search Integration <img src="./utils/images/azure_logo.png" alt="Azure Logo" style="width:30px;height:30px;"/>
Welcome to the Langchain and Azure AI Search Integration Quick Start Accelerator! This repository is your gateway to rapidly developing state-of-the-art AI systems by utilizing the combined strengths of Langchain and Azure AI Search. 


## Project Overview

The core objective of this project is to establish a seamless integration between Langchain and Azure AI Search. This integration is encapsulated in a class named `TextChunkingIndexing`. This class simplifies complex processes and overcomes typical hurdles by offering:

- **PDF, Web Pages, and Text Processing**: Ability to parse and process content from (PDFs)[01-indexing_pdfs.ipynb], (web pages)[02-indexing_from_web.ipynb] (including HTTPS locations), and (text)[03-indexing_from_text.ipynb] from downstream applications.
- **Chunking and Indexing Features**: Functionality to chunk these files, which aids in organizing and structuring the data ultimately boosting relevance.
- **Seamless Indexing into Azure Search**: Tools to efficiently index the processed and chunked files into an Azure Search index.
- **Search Capabilites**: Offering an in-depth walkthrough of the various search options available.
    - **Keyword-Based Search**: Traditional search mechanism focusing on matching exact keywords in the search index.
    + **Semantic Search**: Utilizing Azure AI's natural language processing capabilities to understand the intent and contextual meaning behind search queries, providing more relevant and refined results.
    - **Hybrid Search**: A combination of keyword and semantic search, maximizing the efficiency and accuracy of search results.
    + **Re-ranking**: Advanced feature to dynamically adjust the order of search results based on various criteria, ensuring the most relevant results are prioritized.

This integration is intended to streamline the workflow of handling diverse text sources and optimizing their utility in Azure's powerful search environment.

## Prerequisites 

### 🔧 Dependencies

#### Azure Services
- **Azure AI search**: Delivering Deliver accurate, hyper-personalized responses in your Gen AI applications [start here](https://azure.microsoft.com/en-us/products/ai-services/ai-search/)
- **Azure Open AI Services**: To effectively vectorize data, we leverage the `ada` model within Azure OpenAI Services. This model, part of the suite of large language and generative AI models, is specifically designed for tasks that require nuanced understanding and processing of complex data. By utilizing `ada`, we can transform and represent diverse datasets in a vectorized format. [start here](https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/azure-openai-service-launches-gpt-4-turbo-and-gpt-3-5-turbo-1106/ba-p/3985962)



#### Environment Variables
Add the following keys to your `.env` file (see `.env.sample`)

```plaintext
OPENAI_API_KEY=****
OPENAI_ENDPOINT=****
AZURE_OPENAI_API_VERSION=****
AZURE_SEARCH_SERVICE_ENDPOINT=****
AZURE_SEARCH_ADMIN_KEY=****
```

#### 🌐 Create Conda Environment

Reproducibility is crucial for consistency across environments and ease of collaboration. We use Conda environments to manage env dependencies and ensure uniform functionality across different environemnts. Requirements.txt can be used in your Docker for deployment, ensuring a 1:1 mapping between development and production environments. 

In this project, `make` is utilized to automate the execution of scripts, significantly streamlining the development process.

#### Why Use `make`?

`make` is a powerful build automation tool traditionally used in software development for automating the compilation of executable programs and libraries. It works by reading files called `Makefiles` which define how to build and run tasks.


```bash
make create_conda_env
```

## 🛠 Getting Started



## 🌲 Project Tree Structure

```
📂 gbbai-langchain-azureai-search
┣ 📦 src <- Houses main source code for data processing, feature engineering, modeling, inference, and evaluation. README
┣ 📂 test <- Runs unit and integration tests for code validation and QA. Check README.
┣ 📂 utils <- Contains utility functions and shared code used throughout the project. Detailed info in README
┣ 📜 .pre-commit-config.yaml <- Config for pre-commit hooks ensuring code quality and consistency.
┣ 📜  01-indexing_pdfs.ipynb <- Jupyter notebook detailing the process of indexing PDFs in Azure AI Search.
┣ 📜  02-indexing_from_web.ipynb <- Notebook for indexing content sourced from web pages in Azure AI Search.
┣ 📜  03-indexing_from_text.ipynb <- Demonstrates indexing text data from various sources in Azure AI Search.
┣ 📜  04-searching_ai_search.ipynb <- A guide to implementing and optimizing search functionalities using Azure AI Search sdk.
┣ 📜 CHANGELOG.md <- Logs project changes, updates, and version history.
┣ 📜 CONTRIBUTING.md <- Guidelines for contributing to the project.
┣ 📜 environment.yaml <- Conda environment configuration.
┣ 📜 Makefile <- Simplifies common development tasks and commands.
┣ 📜 pyproject.toml <- Configuration file for build system requirements and packaging-related metadata.
┣ 📜 README.md <- Overview, setup instructions, and usage details of the project.
┣ 📜 requirements-codequality.txt <- Requirements for code quality tools and libraries.
┣ 📜 requirements.txt <- General project dependencies.
```

## 💼 Contributing:

Eager to make significant contributions? Our **[CONTRIBUTING](./CONTRIBUTING.md)** guide is your essential resource! It lays out a clear path.