import os
from langchain.document_loaders import PyPDFLoader
from typing import Dict, List, Optional, Union

import nest_asyncio
import openai
from azure.search.documents.indexes.models import (
    SearchFieldDataType, SearchField, SimpleField, SearchableField, SemanticSettings, SemanticConfiguration, PrioritizedFields, SemanticField
)

from dotenv import load_dotenv
from langchain.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.vectorstores.azuresearch import AzureSearch
from langchain.docstore.document import Document

from utils.ml_logging import get_logger

# Initialize logging
logger = get_logger()

class TextChunkingIndexing:
    """ This class serves as the integration point for chunking and indexing files sourced from web PDFs and plain text from upstream applications.
       It facilitates the process of feeding these data into the Azure AI search index using Langchain integration. 
       The class also provides the flexibility to manually set environment variables or load them from a .env file. """

    def __init__(
        self, 
        openai_api_key: Optional[str] = None, 
        openai_endpoint: Optional[str] = None, 
        azure_openai_api_version: Optional[str] = None,
        azure_ai_search_service_endpoint: Optional[str] = None,
        azure_search_admin_key: Optional[str] = None
    ):
        """
        Initialize the TextChunkingIndexing class with optional environment variables.

        :param openai_api_key: OpenAI API key.
        :param openai_endpoint: OpenAI API endpoint.
        :param azure_openai_api_version: Azure OpenAI API version.
        :param azure_ai_search_service_endpoint: Azure AI Search Service endpoint.
        :param azure_search_admin_key: Azure Search admin key.
        """
        self.openai_api_key = openai_api_key
        self.openai_endpoint = openai_endpoint
        self.azure_openai_api_version = azure_openai_api_version
        self.azure_ai_search_service_endpoint = azure_ai_search_service_endpoint
        self.azure_search_admin_key = azure_search_admin_key

    def load_environment_variables_from_env_file(self):
        """
        Loads required environment variables for the application from a .env file.

        This method should be called explicitly if environment variables are to be loaded from a .env file.
        """
        load_dotenv()

        self.openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.azure_ai_search_service_endpoint = os.getenv("AZURE_AI_SEARCH_SERVICE_ENDPOINT")
        self.azure_search_admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")

        # Check for any missing required environment variables
        missing_vars = [
            var_name for var_name, var in [
                ("AZURE_OPENAI_API_KEY", self.openai_api_key),
                ("AZURE_OPENAI_ENDPOINT", self.openai_endpoint),
                ("AZURE_OPENAI_API_VERSION", self.azure_openai_api_version),
                ("AZURE_AI_SEARCH_SERVICE_ENDPOINT", self.azure_ai_search_service_endpoint),
                ("AZURE_SEARCH_ADMIN_KEY", self.azure_search_admin_key)
            ] if not var
        ]

        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

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
        os.environ["AZURE_OPENAI_API_KEY"] = api_key or self.openai_api_key
        os.environ["AZURE_OPENAI_ENDPOINT"] = resource_endpoint or self.openai_endpoint

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
            logger.info("AzureOpenAIEmbeddings object created successfully.")
            return self.embeddings
        except Exception as e:
            logger.error(f"Error in creating AzureOpenAIEmbeddings object: {e}")
            raise


    def setup_azure_search(
        self,
        endpoint: Optional[str] = None,
        admin_key: Optional[str] = None,
        index_name: str = "langchain-vector-demo",
        fields: Optional[List] = None,
        semantic_settings_config: Optional[List] = None,
    ) -> AzureSearch:
        """
        Creates and configures an AzureSearch instance with the specified parameters or from environment variables.

        If the endpoint or admin_key parameters are not provided, the function attempts to retrieve them from the environment variables.
        If any required parameter is missing, an error is raised.

        The 'fields' and 'semantic_settings' parameters allow for customization of the Azure Search index schema and semantic configurations. 
        If these parameters are not provided, default configurations are used.

        :param endpoint: (optional) The base URL of the Azure Cognitive Search endpoint. Defaults to environment variable.
        :param admin_key: (optional) The admin key for authentication with the Azure Cognitive Search service. Defaults to environment variable.
        :param index_name: (optional) The name of the index to be used. Defaults to "langchain-vector-demo".
        :param fields: (optional) A list of SearchField objects that define the schema of the Azure Search index. If None, a default set is used.
        :param semantic_settings_config: (optional) SemanticSettings object to customize semantic search configurations. If None, a default setting is used.
        :return: Configured AzureSearch object.
        :raises ValueError: If the endpoint or admin_key is missing, or if embeddings are not configured.
        """

        # Default to environment variables if parameters are not provided
        resolved_endpoint = endpoint or self.azure_ai_search_service_endpoint
        resolved_admin_key = admin_key or self.azure_search_admin_key

        # Validate that all required configurations are set
        if not all([resolved_endpoint, resolved_admin_key]):
            missing_params = [
                param
                for param, value in {
                    "endpoint": resolved_endpoint,
                    "admin_key": resolved_admin_key,
                }.items()
                if not value
            ]
            logger.error(f"Missing required parameters: {', '.join(missing_params)}")
            raise ValueError(
                f"Missing required parameters: {', '.join(missing_params)}"
            )
        
        if not self.embeddings:
            raise ValueError("OpenAIEmbeddings object has not been configured. Please call load_embedding_model() first.")
        
        # Use default fields if not provided
        if not fields:
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
                SearchableField(name="content", type=SearchFieldDataType.String, searchable=True),
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=len(self.embeddings.embed_query("Text")),
                    vector_search_configuration="default",
                ),
                SearchableField(name="metadata", type=SearchFieldDataType.String, searchable=True),
                SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="security_group", type=SearchFieldDataType.String, filterable=True),
            ]

        # Use default semantic settings if not provided
        if not semantic_settings_config:
            semantic_settings_config=[
                    SemanticConfiguration(
                        name="config",
                        prioritized_fields=PrioritizedFields(
                            title_field=SemanticField(field_name="content"),
                            prioritized_content_fields=[
                                SemanticField(field_name="content")
                            ],
                            prioritized_keywords_fields=[
                                SemanticField(field_name="metadata")
                            ],
                        ),
                    )
                ]

        self.vector_store = AzureSearch(
            azure_search_endpoint=resolved_endpoint,
            azure_search_key=resolved_admin_key,
            index_name=index_name,
            embedding_function=self.embeddings.embed_query,
            fields=fields,
            semantic_settings=SemanticSettings(default_configuration="config",configurations=semantic_settings_config)
        )

        logger.info("Azure Cognitive Search client configured successfully.")
        return self.vector_store

    @staticmethod
    def split_documents_in_chunks(
        documents: List[Document],
        chunk_size: Optional[int] = 1000,
        chunk_overlap: Optional[int] = 200,
        separators: Optional[List[str]] = None,
        keep_separator: bool = True,
        is_separator_regex: bool = False,
        **kwargs,
    ) -> List[str]:
        """
        Splits text from a list of Document objects into manageable chunks. This method primarily uses character 
        count to determine chunk sizes but can also utilize separators for splitting.
        
        :param documents: List of Document objects to split.
        :param chunk_size: (optional) The number of characters in each text chunk. Defaults to 1000.
        :param chunk_overlap: (optional) The number of characters to overlap between chunks. Defaults to 200.
        :param separators: (optional) List of strings or regex patterns to use as separators for splitting.
        :param keep_separator: (optional) Whether to keep the separators in the resulting chunks. Defaults to True.
        :param is_separator_regex: (optional) Treat the separators as regex patterns. Defaults to False.
        :param kwargs: Additional keyword arguments for customization.
        :return: A list of text chunks.
        :raises Exception: If an error occurs during the text splitting process.
        """

        try:
            # split documents into text and embeddings
            text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            separators=separators,
            keep_separator=keep_separator,
            is_separator_regex=is_separator_regex,
            **kwargs
            )
            chunks = text_splitter.split_documents(documents)
            return chunks
        except Exception as e:
            logger.error(f"Error in scraping and splitting text: {e}")
            raise

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
    def read_and_load_pdfs(pdf_path: str) -> List:
        """
        Reads and loads PDF files from a given path.

        This function checks if the given path is a directory or a file.
        If it's a directory, it goes through the directory and for each file that ends with '.pdf',
        it reads the file, loads its content, and adds it to a list of documents.
        If it's a file, it reads the file, loads its content, and returns a single Document object.

        :param pdf_path: Path to the directory or file containing the PDF files.
        :return: A single Document object if the path is a file, or a list of Document objects if the path is a directory.
        """
        # Convert relative path to absolute path
        pdf_path = os.path.abspath(pdf_path)

        logger.info(f"Reading PDF files from {pdf_path}.")
        
        documents = []
        if os.path.isdir(pdf_path):
            for file in os.listdir(pdf_path):
                if file.endswith('.pdf'):
                    file_path = os.path.join(pdf_path, file)
                    loader = PyPDFLoader(file_path)
                    documents.extend(loader.load())
            return documents
        elif pdf_path.endswith('.pdf'):
            loader = PyPDFLoader(pdf_path)
            documents.extend(loader.load())
            return documents
        else:
            raise ValueError("Invalid path. Path should be a directory or a .pdf file.")


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
            text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, **kwargs)
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
                raise ValueError(
                    "Azure AI Search client has not been configured."
                )

            logger.info(f"Starting to embed and index {len(texts)} chuncks.")
            self.vector_store.add_documents(documents=texts)
            logger.info(f"Successfully embedded and indexed {len(texts)} chuncks.")
        except ValueError as ve:
            logger.error(f"ValueError in embedding and indexing: {ve}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in embedding and indexing: {e}")
            raise
