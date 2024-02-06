# <img src="./utils/images/azure_logo.png" alt="Azure Logo" style="width:30px;height:30px;"/> Azure AI Search: Vectorize and Index Your Data from Multiple Sources and Formats (Preview)

Explore a detailed, step-by-step guide for vectorizing, chunking, loading, indexing and retrieving data from a variety of sources and formats using Azure AI Search.

<p align="center">
    <img src="utils/images/indexing2.png" alt="Indexing_lifecycle" width="950">
</p>


> 📌 **Note**
> Each topic covered in this guide is accompanied by a dedicated Jupyter notebook for a more in-depth..

1. [**Creation of Indexes**](01-creation-indexes.ipynb): This notebook guides you through the process of creating Azure AI Search Indexes.
2. [**Indexing and Vectorizing Content**](02-indexing-vectorized-content.ipynb): This notebook demonstrates how to chunk, vectorize, and index various types of content from multiple sources using OCR and other AI Services.
3. [**Retrieval from Multiple Angles**](03-retrieval.ipynb): This notebook shows different methods of retrieving indexed content from Azure AI Search.
4. [**Quantifying Your Retrievals**](04-evaluation.ipynb): This notebook explains how to measure the relevance and effectiveness of your retrieval system.
5. [**Orchestrating Your Batch Indexing**](05-automation.ipynb): This notebook provides guidance on how to automate and manage your batch indexing process.

## 💡 Why Developers Choose Azure AI Search?

Azure AI Search stands as the premier cloud AI search service, offering unparalleled relevance scoring and reranking capabilities. Leveraging Hybrid Search using Reciprocal Rank Fusion (RRF) alongside state-of-the-art rerankers, it ensures your RAG application's search results are both comprehensive and contextually relevant, backed by SLA's. more [here](https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/azure-cognitive-search-outperforming-vector-search-with-hybrid/ba-p/3929167).

- **Hybrid Search:** Combines the precision of keyword search with the contextual understanding of vector search, delivering highly relevant search results.
- **Semantic Reranking:** Employs advanced algorithms to refine search results, ensuring the most pertinent information tops your search queries.

## 📊 Challenges in Data Indexing to Azure AI Search

Indexing data to Azure AI Search presents several challenges:

- **Integration with External Services**: While Azure AI Search offers robust native connectors with Azure landscape products, expanding integration capabilities with non-Azure services remains a focus area. This project will help you index your data from anywhere using crawl and pull strategies with flexibility for add-ons. For the latest on data connectors, visit [Azure's data source gallery](https://learn.microsoft.com/EN-US/AZURE/search/search-data-sources-gallery).

- **Optimal Chunk Size Determination**: Identifying the ideal chunk size is critical and not easy. Oversized chunks may exceed the model's context window, while undersized ones might lack necessary context.

- **Advanced Content Processing for Sorting**: Achieving efficient retrieval hinges on the sorting strategy's ability to prioritize relevance. This requires sophisticated processing to understand the nuanced context within large datasets.

## 🚀 Approach

The primary goal of this project is to streamline and enhance the integration between various data sources and formats with the Azure AI Search Index. To achieve this, we've introduced a class named `AzureAIndexer`, located in the `src/indexers/ai_search_indexing.py` module. This class simplifies and optimizes the process of text chunking and data transformation, enabling faster iterations and better integrations. It also reduces overhead and addresses mentioned challenges in the process.

<p align="center">
    <img src="utils/images/image.png" alt="AzureAIndexer" width="950">
</p>

> ❗The `AzureAIndexer` class is extensible, allowing for custom logic to be added as needed. Feel free to add methods or modify existing logic to suit your specific use case.

### Key Features of AzureAIndexer

- **Content Processing from Various Sources**: This feature provides the ability to parse and process content from a variety of sources and formats such as PDF, audio, API, text, and more. Using a crawl and push pattern, it allows for pulling data from multiple sources, processing the data, and indexing it in bulk.
- **Chunking Features**: This includes the ability to chunk files, which aids in organizing and structuring the data, ultimately boosting relevance. It offers flexibility to tailor chunk size and overlap, aligning with diverse text processing demands.
- **Out of the box Integration with Document Intelligence and other Azure AI services**: This feature enhances processing of complex documents by integrating with advanced OCR capabilities. It significantly improves the extraction and indexing of data from documents with complex layouts.
- **Seamless Indexing into Azure Search**: This feature enables efficient indexing of the processed and chunked files into an Azure Search index.

### 🛠 Getting Started with `AzureAIndexer`

Initialize the `AzureAIndexer` class:

```python
# Import the AzureAIndexer class from the ai_search_indexing module
from src.indexers.ai_search_indexing import AzureAIndexer

DEPLOYMENT_NAME = "foundational-ada"
INDEX_NAME = "test-index-002"

# Create an instance of the AzureAIndexer class
azure_search_indexer_client = AzureAIndexer(
    index_name=INDEX_NAME, embedding_azure_deployment_name=DEPLOYMENT_NAME
)
```

## 🔧 Prerequisites

Please make sure you have met all the prerequisites for this project. A detailed guide on how to set up your environment and get ready to run all the notebooks and code in this repository can be found in the [REQUIREMENTS.md](REQUIREMENTS.md) file. Please follow the instructions there to ensure a smooth exprience.

## 💼 Contributing:

Eager to make significant contributions? Our **[CONTRIBUTING](./CONTRIBUTING.md)** guide is your essential resource! It lays out a clear path.

## 🔄 Continuous Integration/Continuous Deployment (CI/CD) (preview)

This project leverages GitHub Actions for automating our DevOps lifecycle.

You can view the configuration and status of our GitHub Actions workflows in the `.github/workflows` directory and the "Actions" tab of our GitHub repository, respectively.

## 🌲 Project Tree Structure

```
📂 gbbai-azure-ai-search-indexing
┣ 📦 src <- Houses main source code for data processing, feature engineering, modeling, inference, and evaluation. README
┣ 📂 test <- Runs unit and integration tests for code validation and QA. Check README.
┣ 📂 utils <- Contains utility functions and shared code used throughout the project. Detailed info in README
┣ 📜 .pre-commit-config.yaml <- Config for pre-commit hooks ensuring code quality and consistency.
┣ 📜  01-creation_indexes.ipynb <- This notebook guides you through the process of creating Azure AI Search Indexes.
┣ 📜  02-indexing-vectorized-content.ipynb <- This notebook demonstrates how to chunk, vectorize..
┣ 📜  03-retrieval.ipynb <- This notebook shows different methods of retrieving indexed content from Azure AI Search.
┣ 📜  04-evaluation.ipynb <- This notebook explains how to measure the relevance and effectiveness of your retrieval system.
┣ 📜  05-orchestaration.ipynb <- This notebook provides guidance on how to automate and manage your batch indexing process.
┣ 📜 CHANGELOG.md <- Logs project changes, updates, and version history.
┣ 📜 CONTRIBUTING.md <- Guidelines for contributing to the project.
┣ 📜 environment.yaml <- Conda environment configuration.
┣ 📜 Makefile <- Simplifies common development tasks and commands.
┣ 📜 pyproject.toml <- Configuration file for build system requirements and packaging-related metadata.
┣ 📜 README.md <- Overview, setup instructions, and usage details of the project.
┣ 📜 requirements-codequality.txt <- Requirements for code quality tools and libraries.
┣ 📜 REQUIREMENTS.md <- Prerequisites for this project.
┣ 📜 requirements.txt <- General project dependencies.
```
