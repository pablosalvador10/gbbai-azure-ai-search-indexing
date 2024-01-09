import os
import tempfile
from io import BytesIO
from typing import Any, Dict, List, Optional

from langchain.docstore.document import Document

# Import necessary loader classes
from langchain.document_loaders import (
    CSVLoader,
    DirectoryLoader,
    Docx2txtLoader,
    JSONLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
)

from src.extractors.blob_data_extractor import AzureBlobManager
from utils.ml_logging import get_logger

# Initialize logger
logger = get_logger()


class AzureDocumentLoader:
    def __init__(self, container_name: str):
        """
        Initializes an AzureBlobLoader.

        :param container_name: Name of the blob container.
        """
        try:
            az_manager = AzureBlobManager(container_name=container_name)
            self.container_client = az_manager.container_client
        except Exception as e:
            logger.error(f"Failed to create blob container client: {e}")
            raise

    def download_blob_files(self, filenames: List[str]) -> List[BytesIO]:
        """
        Downloads blobs from a container.

        :param filenames: List of filenames to be downloaded from the blob.
        :return: List of BytesIO objects representing the downloaded blobs.
        """
        blob_data = []
        for filename in filenames:
            try:
                blob_client = self.container_client.get_blob_client(filename)
                if blob_client.exists():
                    blob_data.append(BytesIO(blob_client.download_blob().readall()))
            except Exception as e:
                logger.error(f"Failed to download blob file {filename}: {e}")
        return blob_data

    def write_blob_data_to_temp_files(
        self, blob_data: List[BytesIO], filenames: List[str]
    ) -> List[str]:
        """
        Writes blobs to temporary files.

        :param blob_data: List of BytesIO objects representing the blobs.
        :param filenames: List of filenames corresponding to the blobs.
        :return: List of paths to the temporary files.
        """
        temp_dir = tempfile.mkdtemp()
        temp_files = []
        for i, byteio in enumerate(blob_data):
            try:
                file_path = os.path.join(temp_dir, filenames[i])
                with open(file_path, "wb") as file:
                    file.write(byteio.getbuffer())
                temp_files.append(file_path)
            except Exception as e:
                logger.error(
                    f"Failed to write blob data to temp file {filenames[i]}: {e}"
                )
        return temp_files

    @staticmethod
    def process_files_from_directory(
        temp_dir: str, loader_kwargs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[Document]:
        """
        Loads and processes files from a directory based on their file extension.

        :param temp_dir: Directory containing the files.
        :param loader_kwargs: Optional dictionary of keyword arguments for the loaders.
        :return: List of processed documents.
        """
        if loader_kwargs is None:
            loader_kwargs = {}

        file_type_mappings = {
            "*.txt": TextLoader,
            "*.pdf": PyPDFLoader,
            "*.csv": CSVLoader,
            "*.docx": Docx2txtLoader,
            "*.xlss": UnstructuredExcelLoader,
            "*.xlsx": UnstructuredExcelLoader,
            "*.html": UnstructuredHTMLLoader,
            "*.pptx": UnstructuredPowerPointLoader,
            "*.ppt": UnstructuredPowerPointLoader,
            "*.md": UnstructuredMarkdownLoader,
            "*.json": JSONLoader,
        }
        docs = []
        for glob_pattern, loader_cls in file_type_mappings.items():
            try:
                kwargs = loader_kwargs.get(glob_pattern, {})
                if (
                    loader_cls == JSONLoader
                    and "jq_schema" not in kwargs
                    and "text_content" not in kwargs
                ):
                    kwargs.update({"jq_schema": ".", "text_content": False})
                loader_dir = DirectoryLoader(
                    temp_dir,
                    glob=glob_pattern,
                    loader_cls=loader_cls,
                    loader_kwargs=kwargs,
                    show_progress=False,
                    use_multithreading=True,
                )
                documents = loader_dir.load()
                docs += documents
            except Exception as e:
                logger.error(
                    f"Failed to process files from directory {temp_dir} with glob pattern {glob_pattern}: {e}"
                )
                continue

        return docs

    def load_files_from_blob(
        self,
        filenames: Optional[List[str]] = None,
        loader_kwargs: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[Document]:
        """
        Downloads files from Azure Blob Storage, stores them temporarily, and processes them based on file extension.

        :param filenames: List of filenames to be downloaded from the blob.
        :param loader_kwargs: Optional dictionary of keyword arguments for the loaders.
        :return: Processed documents.
        """
        try:
            blob_data = self.download_blob_files(filenames)
            temp_files = self.write_blob_data_to_temp_files(blob_data, filenames)
            temp_dir = os.path.dirname(
                temp_files[0]
            )  # Get the directory from the first file path
            docs = self.process_files_from_directory(temp_dir, loader_kwargs)
            return docs
        except Exception as e:
            logger.error(f"Failed to load files from blob: {e}")
            raise
