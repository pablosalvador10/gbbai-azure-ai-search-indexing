"""
This module defines the FilesDocumentLoader class which loads and processes documents from paths using OCRDataExtractor.
"""

from typing import Any, Dict, List, Optional, Union

from langchain.docstore.document import Document

from src.extractors.ocr_data_extractors import OCRDataExtractor
from src.loaders.base import DocumentLoaders
from utils.ml_logging import get_logger

# Initialize logger
logger = get_logger()


class OCRFilesDocumentLoader(DocumentLoaders):
    def __init__(self):
        """
        Initializes a DocumentLoaders instance.
        """
        super().__init__()
        self.ocr_data_extractors = OCRDataExtractor()

    def load_document(
        self,
        file_path: Optional[str] = None,
        output_format: Optional[str] = "markdown",
        pages: Optional[str] = None,
        **kwargs: Dict[str, Any],
    ) -> Document:
        """
        Loads a file from a local path, processes it based on its file extension, and updates its metadata.

        :param file_path: The local path of the file to be processed.
        :param output_format: The format of the output.
        :param metadata: A dictionary of metadata to add or update for the processed documents.
        :param kwargs: Optional keyword arguments for the loaders.
        :return: A processed document. Each document will have its metadata updated with the provided metadata.
        :raises ValueError: If 'file_path' is not provided, or if no loader can be found for the provided file extension.
        """
        if not file_path:
            raise ValueError("'file_path' must be provided.")

        content, results_ocr = self.ocr_data_extractors.extract_content(
            file_path, output_format, pages, **kwargs
        )
        metadata = self.ocr_data_extractors.extract_metadata(file_path, results_ocr)

        return Document(page_content=content, metadata=metadata)

    def load_documents(
        self,
        file_paths: Optional[Union[str, List[str]]] = None,
        output_format: Optional[str] = "markdown",
        pages: Optional[str] = None,
        **kwargs,
    ) -> List[Document]:
        """
        Loads files from a local path, processes them based on their file extension, and updates their metadata.

        :param file_paths: The local paths of the files to be processed.
        :param output_format: The format of the output.
        :param metadata: A dictionary of metadata to add or update for the processed documents.
        :return: A list of processed documents. Each document will have its metadata updated with the provided metadata.
        :raises ValueError: If 'file_paths' is not provided, or if no loader can be found for the provided file extension.
        """
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        return [
            doc
            for doc in (
                self.load_document(file_path, output_format, pages, **kwargs)
                for file_path in file_paths
            )
        ]
