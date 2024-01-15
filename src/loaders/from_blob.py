import os
import tempfile
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from langchain.docstore.document import Document
from langchain.document_loaders import DirectoryLoader, JSONLoader

from src.extractors.blob_data_extractors import AzureBlobDataExtractor
from src.loaders.base import DocumentLoaders
from utils.ml_logging import get_logger

# Initialize logger
logger = get_logger()


class FilesDocumentLoader(DocumentLoaders):
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
        super().__init__()
        self.blob_manager = AzureBlobDataExtractor(container_name=container_name)

    def load_document(
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

    def load_document_from_bytes(
        self,
        file_bytes: bytes,
        source_url: str,
        file_extension: Optional[str] = None,
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
                _, file_extension = os.path.splitext(source_url)
            docs = self.load_document(
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

    def load_documents(
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
                        content_bytes = self.blob_manager.extract_content(file_path)
                        metadata = self.blob_manager.extract_metadata(file_path)
                        metadata = self.blob_manager.format_metadata(metadata)
                        documents = self.load_document_from_bytes(
                            content_bytes,
                            source_url=file_path,
                            metadata=metadata,
                            **kwargs,
                        )
                    else:
                        documents = self.load_document(file_url=file_path, **kwargs)
                else:
                    documents = self.load_document(file_path, **kwargs)
                docs += documents
            except Exception as e:
                logger.error(f"Error loading file {file_path}: {e}")
        return docs

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
