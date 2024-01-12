import os
import tempfile
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from langchain.docstore.document import Document
from langchain.document_loaders import DirectoryLoader, JSONLoader

from src.loaders.from_blob import AzureBlobManager
from src.settings import FILE_TYPE_MAPPINGS_LANGCHAIN
from src.utils import get_container_and_blob_name_from_url
from utils.ml_logging import get_logger

# Initialize logger
logger = get_logger()


class DocumentLoaders(AzureBlobManager):
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
        super().__init__(container_name=container_name)
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
        if file_path is None and file_url is None:
            raise ValueError("Either 'file_path' or 'file_url' must be provided.")

        if file_path:
            # Convert relative path to absolute path
            if not file_extension:
                _, file_extension = os.path.splitext(file_path)
            file_path = os.path.abspath(file_path)
            logger.info(f"Reading {file_extension} file from {file_path}.")
        else:
            if not file_extension:
                parsed_url = urlparse(file_url)
                _, file_extension = os.path.splitext(parsed_url.path)
            file_path = file_url
            logger.info(f"Reading {file_extension} file from {file_url}.")

        for pattern, loader_class in FILE_TYPE_MAPPINGS_LANGCHAIN.items():
            if pattern.match(file_extension):
                logger.info(f"Loading file with Loader {loader_class.__name__}")
                docs = loader_class(file_path, **kwargs).load()
                break
        else:
            raise ValueError(f"No loader found for file extension {file_extension}")
        return docs

    def load_file_from_blob(
        self,
        file_name: str,
        container_name: str,
        **kwargs: Dict[str, Any],
    ) -> List[Document]:
        """
        Downloads a file from Azure Blob Storage, stores it temporarily, and processes it based on file extension.

        :param file_name: Name of the file to be downloaded from the blob.
        :param kwargs: Optional keyword arguments for the loaders.
        :return: Processed documents.
        """

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            download_stream = self.blob_service_client.get_blob_client(
                container=container_name, blob=file_name
            ).download_blob()
            temp_file.write(download_stream.readall())

        try:
            _, file_extension = os.path.splitext(file_name)
            docs = self.load_file(
                temp_file.name, file_extension=file_extension, **kwargs
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
        Loads files from the local file system or URLs and processes them based on file extension.

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
                        (
                            container_name,
                            file_name,
                        ) = get_container_and_blob_name_from_url(file_path)
                        documents = self.load_file_from_blob(
                            file_name, container_name, **kwargs
                        )
                    else:
                        documents = self.load_file(file_url=file_path, **kwargs)
                else:
                    documents = self.load_file(file_path, **kwargs)
                docs += documents
            except Exception as e:
                logger.error(f"Error loading file {file_path}: {e}")
        return docs
