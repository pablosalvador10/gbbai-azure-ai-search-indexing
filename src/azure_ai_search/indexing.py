import os
from functools import lru_cache
from typing import List, Optional, Union

import nest_asyncio
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain.document_loaders import PyPDFLoader, WebBaseLoader
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.azuresearch import AzureSearch

from src.azure_ai_search.loaders import AzureDocumentLoader
from src.azure_ai_search.utils import get_container_and_blob_name_from_url
from utils.ml_logging import get_logger

# Initialize logging
logger = get_logger()


class AzureAIndexer:
    """
    This class serves as the integration point for chunking and indexing files sourced from web PDFs and plain
    text from upstream applications. It facilitates the process of feeding these data into the Azure AI search index
    using Langchain integration. The class also provides the flexibility to manually set environment variables or
    load them from a .env file. Additionally, it can load an index from Azure AI Search.
    """

    def __init__(
        self,
        index_name: Optional[str] = None,
        embedding_azure_deployment_name: Optional[str] = None,
        load_environment_variables_from_env_file: bool = True,
        openai_api_key: Optional[str] = None,
        openai_endpoint: Optional[str] = None,
        azure_openai_api_version: Optional[str] = None,
        azure_ai_search_service_endpoint: Optional[str] = None,
        azure_search_admin_key: Optional[str] = None,
    ):
        """
        Initialize the AzureAIChunkIndexer class with optional environment variables.

        :param index_name: The name of the Azure AI Search index to be used.
        :param embedding_azure_deployment_name: The deployment ID for the OpenAI model.
        :param load_environment_variables_from_env_file: A boolean indicating whether to load environment variables from a .env file.
        :param openai_api_key: OpenAI API key.
        :param openai_endpoint: OpenAI API endpoint.
        :param azure_openai_api_version: Azure OpenAI API version.
        :param azure_ai_search_service_endpoint: Azure AI Search Service endpoint.
        :param azure_search_admin_key: Azure Search admin key.
        """
        self.index_name = index_name
        self.embedding_azure_deployment_name = embedding_azure_deployment_name
        self.openai_api_key = openai_api_key
        self.openai_endpoint = openai_endpoint
        self.azure_openai_api_version = azure_openai_api_version
        self.azure_ai_search_service_endpoint = azure_ai_search_service_endpoint
        self.azure_search_admin_key = azure_search_admin_key

        if load_environment_variables_from_env_file:
            self.load_environment_variables_from_env_file()
        if embedding_azure_deployment_name:
            _ = self.load_embedding_model(
                azure_deployment=embedding_azure_deployment_name
            )
        if index_name:
            _ = self.load_azureai_index()

    @lru_cache(maxsize=1)
    def load_environment_variables_from_env_file(self):
        """
        Loads required environment variables for the application from a .env file.

        This method should be called explicitly if environment variables are to be loaded from a .env file.
        """
        load_dotenv()

        self.openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.azure_ai_search_service_endpoint = os.getenv(
            "AZURE_AI_SEARCH_SERVICE_ENDPOINT"
        )
        self.azure_search_admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")

        # Check for any missing required environment variables
        missing_vars = [
            var_name
            for var_name, var in [
                ("AZURE_OPENAI_API_KEY", self.openai_api_key),
                ("AZURE_OPENAI_ENDPOINT", self.openai_endpoint),
                ("AZURE_OPENAI_API_VERSION", self.azure_openai_api_version),
                (
                    "AZURE_AI_SEARCH_SERVICE_ENDPOINT",
                    self.azure_ai_search_service_endpoint,
                ),
                ("AZURE_SEARCH_ADMIN_KEY", self.azure_search_admin_key),
            ]
            if not var
        ]

        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

    def _setup_aoai(
        self,
        api_key: Optional[str] = None,
        resource_endpoint: Optional[str] = None,
    ) -> None:
        """
        Configures the Azure OpenAI API client with the specified parameters.

        Sets the API key and resource endpoint for the OpenAI client to interact with Azure services.

        :param api_key: The API key for authentication with the OpenAI service.
        :param resource_endpoint: The base URL of the Azure OpenAI resource endpoint.
        """
        if api_key is None:
            api_key = self.openai_api_key
        if resource_endpoint is None:
            resource_endpoint = self.openai_endpoint

        if api_key is not None:
            os.environ["AZURE_OPENAI_API_KEY"] = api_key
        if resource_endpoint is not None:
            os.environ["AZURE_OPENAI_ENDPOINT"] = resource_endpoint

    def load_embedding_model(
        self,
        azure_deployment: str,
        api_key: Optional[str] = None,
        resource_endpoint: Optional[str] = None,
        openai_api_version: Optional[str] = None,
        chunk_size: int = 1000,
    ) -> AzureOpenAIEmbeddings:
        """
        Loads and returns an AzureOpenAIEmbeddings object with the specified configuration.

        :param azure_deployment: The deployment ID for the OpenAI model.
        :param model_name: The name of the OpenAI model to use.
        :param api_key: The API key for authentication. Overrides the default if provided.
        :param resource_endpoint: The base URL of the Azure OpenAI resource endpoint. Overrides the default if provided.
        :param openai_api_version: The version of the OpenAI API to be used. Overrides the default if provided.
        :param chunk_size: The size of chunks for processing data. Defaults to 1000.
        :return: Configured AzureOpenAIEmbeddings object.
        """
        logger.info(
            f"Loading OpenAIEmbeddings object with model, deployment {azure_deployment}, and chunk size {chunk_size}"
        )

        self._setup_aoai(api_key, resource_endpoint)

        try:
            self.embeddings = AzureOpenAIEmbeddings(
                azure_deployment=azure_deployment,
                openai_api_version=openai_api_version or self.azure_openai_api_version,
            )
            logger.info(
                """AzureOpenAIEmbeddings object has been created successfully. You can now access the embeddings
                using the '.embeddings' attribute."""
            )
            return self.embeddings
        except Exception as e:
            logger.error(f"Error in creating AzureOpenAIEmbeddings object: {e}")
            raise

    def load_azureai_index(self) -> AzureSearch:
        """
        Configures an existing AzureSearch instance with the specified index name.

        :return: Configured AzureSearch object.
        :raises ValueError: If the AzureSearch instance or embeddings are not configured.
        """

        # Validate that all required configurations are set
        if not all(
            [
                self.azure_ai_search_service_endpoint,
                self.azure_search_admin_key,
                self.index_name,
            ]
        ):
            missing_params = [
                param
                for param, value in {
                    "vector_store_address": self.azure_ai_search_service_endpoint,
                    "vector_store_password": self.azure_search_admin_key,
                    "index_name": self.index_name,
                }.items()
                if not value
            ]
            logger.error(f"Missing required parameters: {', '.join(missing_params)}")
            raise ValueError(
                f"Missing required parameters: {', '.join(missing_params)}"
            )

        if not self.embeddings:
            raise ValueError(
                "OpenAIEmbeddings object has not been configured. Please call load_embedding_model() first."
            )

        self.vector_store = AzureSearch(
            azure_search_endpoint=self.azure_ai_search_service_endpoint,
            azure_search_key=self.azure_search_admin_key,
            index_name=self.index_name,
            embedding_function=self.embeddings.embed_query,
        )

        logger.info(
            f"The Azure AI search index '{self.index_name}' has been loaded correctly."
        )
        return self.vector_store

    @staticmethod
    def scrape_web_text_and_split_by_character(
        urls: List[str],
        chunk_size: Optional[int] = 1000,
        chunk_overlap: Optional[int] = 200,
        **kwargs,
    ) -> List[str]:
        """
        Scrapes text from given URLs and splits it into chunks based on character count with additional customization.

        This function first scrapes text data from the provided URLs using WebBaseLoader.
        It then splits the scraped text into chunks of a specified size with a specified overlap using CharacterTextSplitter.
        Additional keyword arguments can be passed to the splitter for more customization.

        :param urls: List of URLs to scrape text from.
        :param chunk_size: (optional) The number of characters in each text chunk. Defaults to 1000.
        :param chunk_overlap: (optional) The number of characters to overlap between chunks. Defaults to 200.
        :param kwargs: Additional keyword arguments to pass to the CharacterTextSplitter.
        :return: A list of text chunks.
        :raises Exception: If an error occurs during scraping or splitting.
        """
        try:
            nest_asyncio.apply()
            loader = WebBaseLoader(urls)
            scrape_data = loader.load()

            splitter_settings = {
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            }
            splitter_settings.update(kwargs)  # Merge additional keyword arguments

            text_splitter = CharacterTextSplitter(**splitter_settings)
            return text_splitter.split_documents(scrape_data)
        except Exception as e:
            logger.error(f"Error in scraping and splitting text: {e}")
            raise

    @staticmethod
    def read_and_load_pdf(
        pdf_path: Optional[str] = None, pdf_url: Optional[str] = None
    ) -> Union[Document, List[Document]]:
        """
        Reads and loads a single PDF file from a given local path or a URL from Azure Blob Storage.

        This function checks if a local path or a URL is provided.
        If a local path is provided, it reads the file, loads its content, and returns a Document object.
        If a URL is provided, it checks if it's a blob URL. If it is, it downloads the file from Azure Blob Storage,
        reads it, loads its content, and returns a Document object.
        If the URL does not contain "blob.core.windows.net", it treats it as a local file path and follows
        the same logic as if a local path was provided.

        :param pdf_path: Path to the local PDF file.
        :param pdf_url: URL of the PDF file in Azure Blob Storage or a local file path.
        :return: A Document object containing the content of the PDF file.
        """
        if pdf_path is None and pdf_url is None:
            raise ValueError("Either 'pdf_path' or 'pdf_url' must be provided.")

        if pdf_path:
            # Convert relative path to absolute path
            pdf_path = os.path.abspath(pdf_path)

            logger.info(f"Reading PDF file from {pdf_path}.")

            if pdf_path.endswith(".pdf"):
                loader = PyPDFLoader(pdf_path)
                document = loader.load()
                return document
            else:
                raise ValueError("Invalid path. Path should be a .pdf file.")
        elif pdf_url:
            if "blob.core.windows.net" in pdf_url:
                logger.info(f"Downloading and reading PDF file from {pdf_url}.")
                container_name, file_name = get_container_and_blob_name_from_url(
                    pdf_url
                )
                loader = AzureDocumentLoader(container_name=container_name)
                documents = loader.load_files_from_blob(filenames=[file_name])
                return documents
            else:
                logger.info(f"Reading PDF file from {pdf_url}.")

                if pdf_url.endswith(".pdf"):
                    loader = PyPDFLoader(pdf_url)
                    document = loader.load()
                    return document
                else:
                    raise ValueError("Invalid path. Path should be a .pdf file.")
        else:
            raise ValueError("Either a local path or a URL must be provided.")

    def load_and_split_text_by_character_from_pdf(
        self,
        source: Union[str, List[str]],
        chunk_size: int = 1000,
        chunk_overlap: int = 0,
        **kwargs,
    ) -> List[str]:
        """
        Loads text from a file or a blob and splits it into chunks based on character count with additional customization.

        This function can handle text data from a specified file path or directly from a text blob.
        It then splits the loaded text into chunks of a specified size with a specified overlap using CharacterTextSplitter.
        Additional keyword arguments can be passed to the splitter for more customization.

        :param source: Path to the file or a blob containing the text.
        :param chunk_size: (optional) The number of characters in each text chunk. Defaults to 1000.
        :param chunk_overlap: (optional) The number of characters to overlap between chunks. Defaults to 0.
        :param kwargs: Additional keyword arguments to pass to the CharacterTextSplitter.
        :return: A list of text chunks.
        :raises Exception: If an error occurs during loading or splitting.
        """
        try:
            documents = self.read_and_load_pdfs(source)
            text_splitter = CharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap, **kwargs
            )
            return text_splitter.split_documents(documents)
        except Exception as e:
            logger.error(f"Error in loading and splitting text: {e}")
            raise

    def embed_and_index(self, texts: List[str]) -> None:
        """
        Embeds the given texts and indexes them in the configured vector store.

        This method first checks if the vector store (like Azure AI Search) is configured.
        If configured, it proceeds to add the provided texts to the vector store for indexing.

        Args:
            texts (List[str]): A list of text strings to be embedded and indexed.

        Raises:
            ValueError: If the vector store client is not configured.
            Exception: If any other error occurs during the embedding and indexing process.
        """
        try:
            if not self.vector_store:
                raise ValueError("Azure AI Search client has not been configured.")

            logger.info(f"Starting to embed and index {len(texts)} chuncks.")
            self.vector_store.add_documents(documents=texts)
            logger.info(f"Successfully embedded and indexed {len(texts)} chuncks.")
        except ValueError as ve:
            logger.error(f"ValueError in embedding and indexing: {ve}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in embedding and indexing: {e}")
            raise
