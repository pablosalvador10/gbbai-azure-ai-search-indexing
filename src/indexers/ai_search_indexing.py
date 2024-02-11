"""This module contains the AzureAIIndexer class, which handles indexing vectorized content from various sources
and formats using Azure AI services.
"""
import os
from functools import lru_cache
from typing import List, Literal, Optional, Union

import nest_asyncio
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain.document_loaders import WebBaseLoader
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.azuresearch import AzureSearch

from src.chunkers.by_character import CharacterDocumentSplitter
from src.chunkers.by_title import TitleDocumentSplitter
from src.loaders.from_blob import FilesDocumentLoader
from src.loaders.from_ocr import OCRFilesDocumentLoader
from src.loaders.from_sharepoint import SharepointDocumentLoader
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

        self.files_loader_client = FilesDocumentLoader(container_name=None)
        self.sharepoint_loader_client = SharepointDocumentLoader()
        self.character_splitter = CharacterDocumentSplitter()
        self.title_splitter = TitleDocumentSplitter()
        self.ocr_loader_client = OCRFilesDocumentLoader()

    @lru_cache(maxsize=30)
    def load_environment_variables_from_env_file(self):
        """
        Loads required environment variables for the application from a .env file.

        This method should be called explicitly if environment variables are to be loaded from a .env file.
        """
        load_dotenv()

        self.openai_api_key = os.getenv("AZURE_AOAI_API_KEY")
        self.openai_endpoint = os.getenv("AZURE_AOAI_API_ENDPOINT")
        self.azure_openai_api_version = os.getenv("AZURE_AOAI_API_VERSION")
        self.azure_ai_search_service_endpoint = os.getenv(
            "AZURE_AI_SEARCH_SERVICE_ENDPOINT"
        )
        self.azure_search_admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")

        # Check for any missing required environment variables
        missing_vars = [
            var_name
            for var_name, var in [
                ("AZURE_AOAI_API_KEY", self.openai_api_key),
                ("AZURE_AOAI_API_ENDPOINT", self.openai_endpoint),
                ("AZURE_AOAI_API_VERSION", self.azure_openai_api_version),
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
            os.environ["AZURE_AOAI_API_KEY"] = api_key
        if resource_endpoint is not None:
            os.environ["AZURE_AOAI_API_ENDPOINT"] = resource_endpoint

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
                azure_endpoint=resource_endpoint or self.openai_endpoint,
                api_key=api_key or self.openai_api_key,
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

    def load_files_and_split_into_chunks(
        self,
        file_paths: Optional[Union[str, List[str]]] = None,
        splitter_type: Literal[
            "by_title", "by_character_recursive", "by_character_brute_force"
        ] = "recursive",
        use_encoder: bool = True,
        ocr: bool = False,
        chunk_size: int = 512,
        chunk_overlap: int = 128,
        recursive_separators: Optional[List[str]] = None,
        char_separator: Optional[str] = "\n\n",
        keep_separator: bool = True,
        is_separator_regex: bool = False,
        model_name: Optional[str] = "gpt-4",
        verbose: bool = False,
        ocr_output_format: Literal["markdown", "text"] = "markdown",
        section_headings: Optional[List[str]] = None,
        pages: Optional[str] = None,
        **kwargs,
    ) -> List[Document]:
        """
        Loads text from a file or a URL and splits it into manageable chunks based on character count with additional customization.
        If the 'ocr' parameter is set to True, the function will use Optical Character Recognition (OCR) via
        Azure Document Intelligence to extract text from images or scanned documents.

        This function can handle text data from a specified file path or directly from a URL.
        It then splits the loaded text into chunks of a specified size with a specified overlap using the specified splitter.
        Additional keyword arguments can be passed to the splitter for more customization.

        The method can use either RecursiveCharacterTextSplitter, TokenTextSplitter, SpacyTextSplitter,
        or CharacterTextSplitter based on the splitter_type.

        :param file_paths: Path or list of paths of the files to be processed.
        :param splitter_type: The type of splitter to use. Can be "recursive", "tiktoken", "spacy", or "character".
                                                    If not found, the character splitter will be selected. Defaults to "recursive".
        :param use_encoder: Boolean flag to choose whether to use an encoder for the splitter. Defaults to True.
        :param ocr: Boolean flag to enable OCR capabilities for extracting text from images or scanned documents. Defaults to False.
        :param chunk_size: The number of characters in each text chunk. Defaults to 512.
        :param chunk_overlap: The number of characters to overlap between chunks. Defaults to 128.
        :param recursive_separators: List of strings or regex patterns to use as separators for splitting with RecursiveCharacterTextSplitter.
        :param char_separator: String or regex pattern to use as a separator for splitting with CharacterTextSplitter.
        :param keep_separator: Whether to keep the separators in the resulting chunks. Defaults to True.
        :param is_separator_regex: Treat the separators as regex patterns. Defaults to False.
        :param model_name: The name of the model to use for encoding, if use_encoder is True. Defaults to "gpt-4".
        :param verbose: Boolean flag to enable verbose logging. Defaults to False.
        :param kwargs: Additional keyword arguments to pass to the splitter.
        :return: A list of Document objects, each with associated metadata.
        :raises Exception: If an error occurs during loading or splitting.

        The function first loads the documents from the specified file paths using the load_files method of the loader_client.
        Then, it splits the documents into chunks using the split_documents_in_chunks_from_documents function.
        The type of splitter used depends on the splitter_type parameter.
        The size of the chunks and the overlap between them can be customized with the chunk_size and chunk_overlap parameters.
        The separators used for splitting can also be customized with the recursive_separators and char_separator parameters.
        If use_encoder is True, the function uses an encoder for splitting, and the model used for encoding can be
            specified with the model_name parameter.
        """
        try:
            # Define loader clients
            loader_clients = {
                "ocr": {
                    "client": self.ocr_loader_client,
                    "params": {
                        "file_paths": file_paths,
                        "output_format": ocr_output_format,
                        "pages": pages,
                        **kwargs,
                    },
                },
                "files": {
                    "client": self.files_loader_client,
                    "params": {"file_paths": file_paths, **kwargs},
                },
            }

            # Choose the loader client
            loader_key = "ocr" if ocr else "files"
            loader_client = loader_clients.get(loader_key, loader_clients["files"])

            # Load documents
            try:
                documents = loader_client["client"].load_documents(
                    **loader_client["params"]
                )
            except Exception as e:
                raise Exception(f"An error occurred during loading documents: {str(e)}")

            # Define splitter methods
            splitter_methods = {
                "by_title": {
                    "method": self.title_splitter.split_documents_in_chunks_from_documents,
                    "params": {
                        "documents": documents,
                        "chunk_size": chunk_size,
                        "section_headings": section_headings,
                    },
                },
                "default": {
                    "method": self.character_splitter.split_documents_in_chunks_from_documents,
                    "params": {
                        "documents": documents,
                        "splitter_type": splitter_type,
                        "use_encoder": use_encoder,
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap,
                        "recursive_separators": recursive_separators,
                        "char_separator": char_separator,
                        "keep_separator": keep_separator,
                        "is_separator_regex": is_separator_regex,
                        "model_name": model_name,
                        "verbose": verbose,
                        **kwargs,
                    },
                },
            }

            # Choose the splitter method
            splitter_key = (
                "default"
                if splitter_type
                in ["by_character_recursive", "by_character_brute_force"]
                else splitter_type
            )
            splitter_method = splitter_methods.get(
                splitter_key, splitter_methods["default"]
            )

            # Split documents into chunks
            try:
                chunks = splitter_method["method"](**splitter_method["params"])
            except Exception as e:
                raise Exception(
                    f"An error occurred during splitting documents: {str(e)}"
                )

            return chunks
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {str(e)}")

    def load_files_and_split_into_chunks_from_sharepoint(
        self,
        site_name: str,
        site_domain: str,
        file_names: Union[str, List[str]],
        splitter_type: str = "recursive",
        use_encoder: bool = True,
        chunk_size: int = 512,
        chunk_overlap: int = 128,
        recursive_separators: Optional[List[str]] = None,
        char_separator: Optional[str] = "\n\n",
        keep_separator: bool = True,
        is_separator_regex: bool = False,
        model_name: Optional[str] = "gpt-4",
        verbose: bool = False,
        **kwargs,
    ) -> List[Document]:
        """
        Loads text from SharePoint and splits it into manageable chunks based on character count with additional customization.

        :param file_names: Name or list of names of the files to be processed.
        :param site_name: Name of the SharePoint site where the files are located.
        :param site_domain: Domain of the SharePoint site where the files are located.
        :param splitter_type: The type of splitter to use. Can be "recursive", "tiktoken", "spacy", or "character".
                            If not found, the character splitter will be selected. Defaults to "recursive".
        :param use_encoder: Boolean flag to choose whether to use an encoder for the splitter. Defaults to True.
        :param chunk_size: The number of characters in each text chunk. Defaults to 512.
        :param chunk_overlap: The number of characters to overlap between chunks. Defaults to 128.
        :param recursive_separators: List of strings or regex patterns to use as separators for splitting with RecursiveCharacterTextSplitter.
        :param char_separator: String or regex pattern to use as a separator for splitting with CharacterTextSplitter.
        :param keep_separator: Whether to keep the separators in the resulting chunks. Defaults to True.
        :param is_separator_regex: Treat the separators as regex patterns. Defaults to False.
        :param model_name: The name of the model to use for encoding, if use_encoder is True. Defaults to "gpt-4".
        :param verbose: Boolean flag to enable verbose logging. Defaults to False.
        :param kwargs: Additional keyword arguments to pass to the splitter.
        :return: A list of Document objects, each with associated metadata.
        :raises Exception: If an error occurs during loading or splitting.
        """
        documents = self.sharepoint_loader_client.load_documents(
            site_name=site_name,
            site_domain=site_domain,
            file_names=file_names,
            **kwargs,
        )
        try:
            chunks = self.character_splitter.split_documents_in_chunks_from_documents(
                documents=documents,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                recursive_separators=recursive_separators,
                char_separator=char_separator,
                keep_separator=keep_separator,
                is_separator_regex=is_separator_regex,
                splitter_type=splitter_type,
                use_encoder=use_encoder,
                model_name=model_name,
                verbose=verbose,
                **kwargs,
            )
            return chunks
        except Exception as e:
            logger.error(f"Error in splitting documents into chunks: {e}")
            raise

    def index_text_embeddings(self, text_list: List[str]) -> bool:
        """
        Generates embeddings for the given texts and indexes them in the configured vector store.

        This method first verifies if the vector store (like Azure AI Search) is configured.
        If configured, it proceeds to add the provided texts to the vector store for indexing.

        Args:
            text_list (List[str]): A list of text strings for which embeddings are to be generated and indexed.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            if not self.vector_store:
                logger.warning("Vector store client is not configured.")
                return False

            logger.info(
                f"Embedding and indexing initiated for {len(text_list)} text chunks."
            )
            self.vector_store.add_documents(documents=text_list)
            logger.info(
                f"Embedding and indexing completed for {len(text_list)} text chunks."
            )
            return True
        except Exception as e:
            logger.error(
                f"Unexpected error occurred during embedding and indexing: {e}"
            )
            return False
