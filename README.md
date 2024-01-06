# <img src="./utils/images/azure_logo.png" alt="Azure Logo" style="width:30px;height:30px;"/> Vectorize and Index your data from multiple sources

This repository offers an efficient solution for rapidly indexing data from various sources into Azure AI Search in a vectorized manner. By making the vectorization process straightforward, it allows you to leverage the sophisticated search capabilities of Azure AI Search (Hybrid + Rerank) to the fullest. This not only boosts your retrieval scores but also accelerates the optimization phase in your Retrieval Augmented Generation (RAG) development stage.

## Table of Contents

- [Indexing your vectorized data from multiple sources](#indexing-your-vectorized-data-from-multiple-sources)
    - [Understanding Challenges Indexing into Azure AI Search with LLMs](#understanding-challenges-indexing-into-azure-ai-search-with-llms)
    - [Solution](#solution)
    - [Getting Started with `TextChunkingIndexing`](#getting-started-with-textchunkingindexing)
- [Prerequisites](#prerequisites)
    - [Setting Up Your Azure Services](#setting-up-your-azure-services)
    - [Configuring Your Environment Variables](#configuring-your-environment-variables)
    - [Create Conda Environment](#create-conda-environment)
- [Project Tree Structure](#project-tree-structure)
- [Contributing](#contributing)

## 🔍 Understanding Challenges Indexing into Azure AI Search with LLMs

**🧩 Fragmented Information**

Fragmentation is a notable issue when indexing large documents, especially in contexts where similar terms are scattered in different sections. This can lead to confusion and misinformation due to improper context understanding. The relevance of retrieved information heavily relies on the effectiveness of chunking and sorting strategies implemented.

#### 📊 Data Chunking and Sorting:

**📏 Optimal Chunk Size**: The challenge lies in determining the right chunk size for documents. If a chunk is too large, it may surpass the model's context window, causing loss of information. Conversely, too small a chunk might lack necessary context, leading to ineffective indexing and retrieval.

**🔀 Effective Sorting Strategies**: Efficient retrieval is contingent upon how well the chunks are sorted. Prioritizing relevance in sorting is crucial but poses a challenge due to the nuanced understanding required by LLMs in discerning context and relevance within large datasets.

**🔗 Overlap Consideration**: Implementing overlapping chunks is critical for maintaining continuity and preserving context, especially in lengthy documents or complex subject matters. This requires a delicate balance to ensure that information is not fragmented or lost.

> 📌 **Note**
>
> Adjusting chunk sizes and overlaps is vital for high-quality text retrieval, especially in precision-based search applications like RAGs. Learn more about fine-tuning and relevance scores [here](https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/azure-cognitive-search-outperforming-vector-search-with-hybrid/ba-p/3929167).

## 🚀 Solution

The primary goal of this project is to facilitate a smooth integration between multiple data sources and formats and Azure AI Search Index. To achieve this, we've introduced a class named `TextChunkingIndexing`, located in the `src/gbb_ai/text_chunking_indexing.py` module. This class is designed to simplify and optimize the process of text chunking and indexing, overcoming common challenges in the process.

> ❗The `TextChunkingIndexing` class is extensible, allowing for custom logic to be added as needed. Feel free to add methods or modify existing logic to suit your specific use case.

### Key Features of TextChunkingIndexing

- **PDF, Docs, Web Pages, and Text Processing**: provides the ability to parse and process content from various sources including [PDFs](01-indexing_pdfs.ipynb), [web pages](02-indexing_from_web.ipynb) (including HTTPS locations), and [text](03-indexing_from_text.ipynb) or files from various applications such as SharePoint and Blob Storage.
- **Chunking and Indexing Features**: Functionality to chunk these files, which aids in organizing and structuring the data ultimately boosting relevance. Offers flexibility to tailor chunk size and overlap, aligning with diverse text processing demands.
- **Seamless Indexing into Azure Search**: efficiently index the processed and chunked files into an Azure Search index.

Also, we'll laverage the Azure AI search sdk and offering an in-depth walkthrough of the various search options available.

### 🛠 Getting Started with `TextChunkingIndexing`

This class serves as a standalone wrapper, simplifying the integration of LangChain and Azure AI Search. It streamlines the process of retrieving, storing, and indexing textual data from web and document sources into Azure AI Search.

Initialize the `TextChunkingIndexing` class:

```python
# Import the TextChunkingIndexing class from the langchain_integration module
from src.gbb_ai.langchain_integration_azureai import TextChunkingIndexing

# Create an instance of the TextChunkingIndexing class
gbb_ai_indexer = TextChunkingIndexing()

# Load the environment variables from the .env file
gbb_ai_indexer.load_environment_variables_from_env_file()
```

## ❗Prerequisites

#### Setting Up Your Azure Services

- **Azure AI search**: Delivering Deliver accurate, hyper-personalized responses in your Gen AI applications [start here](https://azure.microsoft.com/en-us/products/ai-services/ai-search/)
- **Azure Open AI Services**: To effectively vectorize data, we leverage the `ada` model within Azure OpenAI Services. This model, part of the suite of large language and generative AI models, is specifically designed for tasks that require nuanced understanding and processing of complex data. By utilizing `ada`, we can transform and represent diverse datasets in a vectorized format. [start here](https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/azure-openai-service-launches-gpt-4-turbo-and-gpt-3-5-turbo-1106/ba-p/3985962)

#### Configuring Your Environment Variables

We use the `.env` file to securely store and manage sensitive configuration data such as API keys, database credentials, and other environment-specific settings. This data is then loaded into the environment at runtime, making it accessible to our application without exposing it in the code or version control. This approach not only enhances security but also provides flexibility, as you can easily change the configuration for different environments (e.g., development, testing, production) by simply updating the `.env` file.

```plaintext
OPENAI_API_KEY=****
OPENAI_ENDPOINT=****
AZURE_OPENAI_API_VERSION=****
AZURE_SEARCH_SERVICE_ENDPOINT=****
AZURE_SEARCH_ADMIN_KEY=****
```

#### 🐍 Create Conda Environment

Reproducibility is crucial for consistency across environments and ease of collaboration. We use Conda environments to manage dependencies and ensure uniform functionality across different environments. The `requirements.txt` file can be used in your Docker for deployment, ensuring a 1:1 mapping between development and production environments.

In this project, we utilize `make` to automate the execution of scripts, significantly streamlining the development process.

##### Automation with `make`

`make` is a powerful build automation tool traditionally used in software development for automating the compilation of executable programs and libraries. It works by reading files called `Makefiles` which define how to derive the target program.

```bash
make create_conda_env
```

For Windows users, if `make` is not available, you can leverage Conda's built-in commands to create and activate the environment. The `environment.yaml` file in this project contains the necessary configuration to set up your Conda environment.

To create the environment, use the following command in your command prompt:

```bash
conda env create -f environment.yaml
```

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
