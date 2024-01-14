import os
import tempfile
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from langchain.docstore.document import Document
from langchain.document_loaders import DirectoryLoader, JSONLoader

from src.extractors.blob_data_extractors import AzureBlobDataExtractor
from src.extractors.sharepoint_data_extractor import SharePointDataExtractor
from src.loaders.settings import FILE_TYPE_MAPPINGS_LANGCHAIN
from src.utils import get_container_and_blob_name_from_url
from utils.ml_logging import get_logger

# Initialize logger
logger = get_logger()


class DocumentLoaders:
    """
    This class uses a mapping of file types to specific loader classes, which are used to load
    and parse the documents. The mapping can be customized to support additional file types.
    """

    def __init__(self, container_name: Optional[str] = None):
        """
        Initializes a DocumentLoaders instance.

        :param container_name: Name of the Azure Blob Storage container. If provided, the AzureDocumentLoader
        is initialized with this container name.
        """
        self.blob_manager = AzureBlobDataExtractor(container_name=container_name)
        self.sharepoint_manager = SharePointDataExtractor()
        self.langchain_file_mapping = FILE_TYPE_MAPPINGS_LANGCHAIN

    def process_files_from_directory(
        self, dir: str, **loader_kwargs: Dict[str, Any]
    ) -> List[Document]:
        """
        Loads and processes files from a directory based on their file extension.

        :param temp_dir: Directory containing the files.
        :param loader_kwargs: Optional keyword arguments for the loaders.
        :return: List of processed documents.
        """
        docs = []
        for glob_pattern, loader_cls in self.langchain_file_mapping.items():
            print(f"what is the {glob_pattern}")
            try:
                kwargs = loader_kwargs.get(glob_pattern, {})
                if (
                    loader_cls == JSONLoader
                    and "jq_schema" not in kwargs
                    and "text_content" not in kwargs
                ):
                    kwargs.update({"jq_schema": ".", "text_content": False})
                loader_dir = DirectoryLoader(
                    dir,
                    glob=glob_pattern,
                    loader_cls=loader_cls,
                    loader_kwargs=kwargs,
                    show_progress=False,
                    use_multithreading=True,
                )
                documents = loader_dir.load()
                docs += documents
                logger.info(
                    f"Try loaded files from {dir} with glob pattern {glob_pattern}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to process files from directory {dir} with glob pattern {glob_pattern}: {e}"
                )
                continue
        return docs

    def load_file(
        self,
        file_path: Optional[str] = None,
        file_url: Optional[str] = None,
        file_extension: Optional[str] = None,
        source_url: Optional[str] = None,
        **kwargs: Dict[str, Any],
    ) -> List[Document]:
        """
        Loads a file from the local file system or a URL and processes it based on file extension.

        :param file_path: Path of the file to be processed.
        :param file_url: URL of the file to be processed.
        :param file_extension: Extension of the file to be processed.
        :param kwargs: Optional keyword arguments for the loaders.
        :return: Processed documents.
        """
        if not file_path and not file_url:
            raise ValueError("Either 'file_path' or 'file_url' must be provided.")

        if file_path:
            # Convert relative path to absolute path
            file_path = os.path.abspath(file_path)

            # Determine file extension if not provided
            if not file_extension:
                _, file_extension = os.path.splitext(file_path)
            # Log the source of the file
            if source_url:
                logger.info(
                    f"Reading {file_extension} file from temporary location {file_path} originally sourced from {source_url}."
                )
            else:
                logger.info(
                    f"Reading {file_extension} file from local path {file_path}."
                )
        else:
            if not file_extension:
                parsed_url = urlparse(file_url)
                _, file_extension = os.path.splitext(parsed_url.path)
            file_path = file_url
            logger.info(f"Reading {file_extension} file from {file_url}.")

        for pattern, loader_class in FILE_TYPE_MAPPINGS_LANGCHAIN.items():
            if pattern.match(file_extension):
                logger.info(f"Loading file with Loader {loader_class.__name__}")
                if not source_url:
                    docs = loader_class(file_path, **kwargs).load()
                else:
                    # TODO: improve this logic for more formats
                    loader = loader_class(file_path, **kwargs)
                    loader.web_path = source_url
                    docs = loader.load()
                break
        else:
            raise ValueError(f"No loader found for file extension {file_extension}")
        return docs

    def load_file_from_blob(
        self,
        file_path: str,
        **kwargs: Dict[str, Any],
    ) -> List[Document]:
        """
        Downloads a file from Azure Blob Storage, stores it temporarily, and processes it based on file extension.

        :param file_name: Name of the file to be downloaded from the blob.
        :param kwargs: Optional keyword arguments for the loaders.
        :return: Processed documents.
        """

        (
            container_name,
            file_name,
        ) = get_container_and_blob_name_from_url(file_path)

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            download_stream = self.blob_manager.blob_service_client.get_blob_client(
                container=container_name, blob=file_name
            ).download_blob()
            temp_file.write(download_stream.readall())

        try:
            _, file_extension = os.path.splitext(file_name)
            docs = self.load_file(
                temp_file.name,
                file_extension=file_extension,
                source_url=file_path,
                **kwargs,
            )

        finally:
            try:
                os.remove(temp_file.name)
                logger.info(f"Deleted temporary file: {temp_file.name}")
            except OSError as e:
                logger.warning(f"Error deleting temporary file: {e}")

        return docs

    def load_file_from_sharepoint(
        self,
        file_name: str,
        site_domain: str,
        site_name: str,
        **kwargs: Dict[str, Any],
    ) -> List[Document]:
        """
        Downloads a file from SharePoint, stores it temporarily, and processes it based on file extension.

        :param file_name: Name of the file to be downloaded from SharePoint.
        :param site_domain: The domain of the SharePoint site.
        :param site_name: The name of the SharePoint site.
        :param kwargs: Optional keyword arguments for the loaders.
        :return: Processed documents.
        :raises ValueError: If the file is not found in the SharePoint site.
        """
        logger.info("Loading environment variables from .env file.")
        self.sharepoint_manager.load_environment_variables_from_env_file()

        logger.info("Authenticating with Microsoft Graph.")
        self.sharepoint_manager.msgraph_auth()

        if self.sharepoint_manager._are_required_variables_missing():
            logger.error("Required environment variables are missing.")
            raise ValueError("Required environment variables are missing.")

        logger.info("Getting site and drive IDs.")
        site_id, drive_id = self.sharepoint_manager._get_site_and_drive_ids(
            site_domain, site_name
        )
        if not site_id or not drive_id:
            logger.error("Site ID or Drive ID is missing.")
            raise ValueError("Site ID or Drive ID is missing.")

        logger.info("Getting files in site.")
        files = self.sharepoint_manager.get_files_in_site(
            site_id, drive_id, folder_path=None, minutes_ago=None, file_formats=None
        )

        matching_files = [file for file in files if file.get("name") == file_name]
        if not matching_files:
            logger.error(f"No file found with the name {file_name}")
            raise ValueError(f"No file found with the name {file_name}")

        logger.info("Extracting file metadata.")
        metadata = self.sharepoint_manager._extract_file_metadata(matching_files[0])

        logger.info(f"Metadata: {metadata}")

        logger.info("Getting file content bytes.")
        file_bytes = self.sharepoint_manager.get_file_content_bytes(
            site_id=site_id, drive_id=drive_id, file_name=file_name, folder_path=None
        )

        logger.info("Loading file from bytes.")
        docs = self.load_file_from_bytes(
            file_bytes=file_bytes, file_path=metadata.get("webUrl"), **kwargs
        )

        logger.info("File loaded successfully.")
        return docs

    def load_file_from_bytes(
        self,
        file_bytes: bytes,
        file_path: Optional[str] = None,
        **kwargs: Dict[str, Any],
    ) -> List[Document]:
        """
        Loads a file from bytes and processes it based on file extension.

        :param file_bytes: Bytes of the file to be processed.
        :param file_path: Path of the file to be processed.
        :param kwargs: Optional keyword arguments for the loaders.
        :return: Processed documents.
        :raises ValueError: If file_path is None.
        """
        if file_path is None:
            raise ValueError("'file_path' must be provided.")

        if "?action=default&mobileredirect=true" in file_path:
            file_path_test = file_path.split("?action=default&mobileredirect=true")[0]
            _, file_extension = os.path.splitext(file_path_test)

        else:
            _, file_extension = os.path.splitext(file_path)

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_bytes)
            temp_file.flush()

        try:
            _, file_extension = os.path.splitext(file_path)
            docs = self.load_file(
                file_path=temp_file.name,
                file_extension=file_extension,
                source_url=file_path,
                **kwargs,
            )

        finally:
            try:
                os.remove(temp_file.name)
                logger.info(f"Deleted temporary file: {temp_file.name}")
            except OSError as e:
                logger.warning(f"Error deleting temporary file: {e}")

        return docs

    def load_files(
        self, file_paths: Optional[Union[str, List[str]]] = None, **kwargs
    ) -> Union[Document, List[Document]]:
        """
        Loads files from the local file system, URLs, or SharePoint and processes them based on file extension.

        :param file_paths: Path or list of paths of the files to be processed.
        :param kwargs: Optional keyword arguments for the loaders.
        :return: Processed documents.
        """
        if not file_paths:
            raise ValueError("'file_paths' must be provided.")

        docs = []

        if isinstance(file_paths, str):
            file_paths = [file_paths]

        for file_path in file_paths:
            try:
                if file_path.startswith(("http", "https")):
                    if "blob.core.windows.net" in file_path:
                        documents = self.load_file_from_blob(file_path, **kwargs)
                    else:
                        documents = self.load_file(file_url=file_path, **kwargs)
                else:
                    documents = self.load_file(file_path, **kwargs)
                docs += documents
            except Exception as e:
                logger.error(f"Error loading file {file_path}: {e}")
        return docs
