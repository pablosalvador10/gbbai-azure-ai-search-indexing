import os
import tempfile
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from langchain.docstore.document import Document

from src.extractors.sharepoint_data_extractor import SharePointDataExtractor
from src.loaders.base import DocumentLoaders
from utils.ml_logging import get_logger

# Initialize logger
logger = get_logger()


class SharepointDocumentLoader(DocumentLoaders):
    """
    This class uses a mapping of file types to specific loader classes, which are used to load
    and parse the documents. The mapping can be customized to support additional file types.
    """

    def __init__(self):
        """
        Initializes a DocumentLoaders instance.

        :param container_name: Name of the Azure Blob Storage container. If provided, the AzureDocumentLoader
        is initialized with this container name.
        """
        super().__init__()
        self.sharepoint_manager = SharePointDataExtractor()
        logger.debug("Loading environment variables from .env file.")
        self.sharepoint_manager.load_environment_variables_from_env_file()

        logger.debug("Authenticating with Microsoft Graph.")
        self.sharepoint_manager.msgraph_auth()

    def load_file_from_bytes(
        self,
        file_bytes: bytes,
        file_extension: Optional[str] = None,
        source_url: Optional[str] = None,
        file_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Dict[str, Any],
    ) -> List[Document]:
        """
        Loads a file from bytes and processes it based on file extension.

        :param file_bytes: Bytes of the file to be processed.
        :param file_extension: Extension of the file to be processed.
        :param source_url: URL where the file was downloaded from.
        :param file_name: Name of the file to be processed.
        :param kwargs: Optional keyword arguments for the loaders.
        :return: Processed documents.
        """

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_bytes)
            temp_file.flush()

        try:
            if not file_extension:
                _, file_extension = os.path.splitext(file_name or source_url)
            docs = self.load_file(
                file_path=temp_file.name,
                file_extension=file_extension,
                source_url=source_url,
                metadata=metadata,
                **kwargs,
            )

        finally:
            try:
                os.remove(temp_file.name)
                logger.info(f"Deleted temporary file: {temp_file.name}")
            except OSError as e:
                logger.warning(f"Error deleting temporary file: {e}")

        return docs

    def load_file(
        self,
        file_path: Optional[str] = None,
        file_url: Optional[str] = None,
        file_extension: Optional[str] = None,
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Dict[str, Any],
    ) -> List[Document]:
        """
        Loads a file from a local path or a URL, processes it based on its file extension, and updates its metadata.

        :param file_path: The local path of the file to be processed. This should be provided if the file is located on the local file system.
        :param file_url: The URL of the file to be processed. This should be provided if the file is to be downloaded from a URL.
        :param file_extension: The extension of the file to be processed. If not provided, it will be inferred from the file path or URL.
        :param source_url: The URL where the file was originally sourced from. This will be added to the metadata of the processed documents.
        :param metadata: A dictionary of metadata to add or update for the processed documents. This can be used to provide
          additional information about the documents.
        :param kwargs: Optional keyword arguments for the loaders. These will be passed to the loader that processes the file.
        :return: A list of processed documents. Each document will have its metadata updated with the provided metadata and source URL.
        :raises ValueError: If neither 'file_path' nor 'file_url' is provided, or if no loader can be found for the provided file extension.
        """
        if not file_path and not file_url:
            raise ValueError("Either 'file_path' or 'file_url' must be provided.")

        if file_path:
            file_path = os.path.abspath(file_path)
            if not file_extension:
                _, file_extension = os.path.splitext(file_path)
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

        for pattern, loader_class in self.langchain_file_mapping.items():
            if pattern.match(file_extension):
                logger.info(f"Loading file with Loader {loader_class.__name__}")
                docs = loader_class(file_path, **kwargs).load()

                # Update or add metadata for each document
                for doc in docs:
                    if not doc.metadata:
                        doc.metadata = {}
                    if metadata:
                        doc.metadata.update(metadata)
                    if source_url:
                        doc.metadata["source"] = source_url
                break
        else:
            raise ValueError(f"No loader found for file extension {file_extension}")
        return docs

    def load_document(
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
        if self.sharepoint_manager._are_required_variables_missing():
            logger.error("Required environment variables are missing.")
            raise ValueError("Required environment variables are missing.")

        logger.debug("Getting site and drive IDs.")
        site_id, drive_id = self.sharepoint_manager.get_site_and_drive_ids(
            site_domain, site_name
        )
        if not site_id or not drive_id:
            logger.debug("Site ID or Drive ID is missing.")
            raise ValueError("Site ID or Drive ID is missing.")

        logger.debug("Getting files in site.")
        files = self.sharepoint_manager.get_files_in_site(
            site_id, drive_id, folder_path=None, minutes_ago=None, file_formats=None
        )

        matching_files = [file for file in files if file.get("name") == file_name]
        if not matching_files:
            logger.error(f"No file found with the name {file_name}")
            raise ValueError(f"No file found with the name {file_name}")

        logger.debug("Extracting file metadata.")
        metadata = self.sharepoint_manager.extract_metadata(matching_files[0])

        logger.debug(f"Metadata: {metadata}")

        logger.debug("Getting file content bytes.")
        file_bytes = self.sharepoint_manager.extract_content(
            site_id=site_id, drive_id=drive_id, file_name=file_name, folder_path=None
        )

        logger.debug("Loading file from bytes.")
        docs = self.load_file_from_bytes(
            file_bytes=file_bytes,
            file_name=file_name,
            source_url=metadata.get("webUrl"),
            metadata=metadata,
            **kwargs,
        )

        logger.debug("File loaded successfully.")
        return docs

    def load_documents(
        self,
        file_names: Union[str, List[str]],
        site_domain: str,
        site_name: str,
        **kwargs,
    ) -> Union[Document, List[Document]]:
        """
        Loads multiple files from SharePoint and processes them based on file extension.

        This method accepts a list of file names and iterates over them, calling the `load_file` method for each one.
        If an error occurs while loading a file, it logs the error and continues with the next file.
        If no documents were loaded from any of the files, it logs an error and returns an empty list.

        :param file_names: A single file name or a list of file names to load.
        :param site_domain: The domain of the SharePoint site.
        :param site_name: The name of the SharePoint site.
        :param kwargs: Additional keyword arguments to pass to the `load_file` method.
        :return: A list of Document objects loaded from the files. If no documents were loaded, returns an empty list.
        :raises Exception: If an error occurs while loading a file.
        """

        if isinstance(file_names, str):
            file_names = [file_names]

        documents = []
        for file_name in file_names:
            try:
                docs = self.load_document(
                    file_name=file_name,
                    site_domain=site_domain,
                    site_name=site_name,
                    **kwargs,
                )
                if docs:
                    documents += docs
                else:
                    logger.error(f"No documents were loaded from file {file_name}.")
            except Exception as e:
                logger.error(f"Error loading file {file_name}: {e}")

        if not documents:
            logger.error("No documents were loaded.")
            return []
        return documents
