"""
This module defines the OCRDataExtractor class for extracting content and metadata from various file formats
using Azure Document Intelligence for Optical Character Recognition (OCR).
"""
import os
import warnings
from typing import Any, Dict, Optional, Tuple, Union

from dotenv import load_dotenv

from src.enrichers.ocr_document_intelligence import AzureDocumentIntelligenceManager
from src.extractors.base import DataExtractor
from utils.ml_logging import get_logger

# Initialize logger
logger = get_logger()

MODEL_TYPE = "prebuilt-layout"


class OCRDataExtractor(DataExtractor):
    """
    Class for managing interactions with Azure Document Intelligence. It provides functionalities
    to extract content and metadata from various file formats using OCR.

    Attributes:
        az_intel (AzureDocumentIntelligenceManager): Azure Document Intelligence Manager.
    """

    def __init__(
        self, azure_endpoint: Optional[str] = None, azure_key: Optional[str] = None
    ):
        """
        Initialize the OCRDataExtractor with Azure Document Intelligence credentials.

        Args:
            azure_endpoint (str, optional): Azure Document Intelligence endpoint. Defaults to None.
            azure_key (str, optional): Azure Document Intelligence key. Defaults to None.
        """
        try:
            load_dotenv()
            azure_endpoint = azure_endpoint or os.getenv(
                "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
            )
            azure_key = azure_key or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
            self.az_intel = AzureDocumentIntelligenceManager(
                azure_endpoint=azure_endpoint, azure_key=azure_key
            )
        except Exception as e:
            logger.error(f"Error initializing OCRDataExtractor: {e}")
            raise

    def extract_content(
        self,
        file_path: str,
        output_format: str = "markdown",
        pages: Optional[str] = None,
        **kwargs,
    ) -> Tuple[Dict[str, Any], Any]:
        """
        Extracts content from a file using Azure Document Intelligence.

        :param file_path: Path of the file to be processed.
        :param output_format: Desired output format of the extracted content.
        :param kwargs: Optional keyword arguments for the analyze_document method.
        :return: Tuple containing a dictionary representing the extracted content and the OCR result.
        """
        try:
            self.result_ocr = self.az_intel.analyze_document(
                document_input=file_path,
                model_type=MODEL_TYPE,
                output_format=output_format,
                pages=pages,
                features=["OCR_HIGH_RESOLUTION"],
                **kwargs,
            )

            # Check if result_ocr.content is empty
            if not self.result_ocr.content:
                warnings.warn("result_ocr.content is empty")
            else:
                logger.info(f"Successfully extracted content from {file_path}")
        except Exception as e:
            logger.error(f"Failed to extract content from file {file_path}: {e}")
        return self.result_ocr.content, self.result_ocr

    def extract_metadata(
        self, file_path: str, result_ocr: Any
    ) -> Dict[str, Optional[Union[str, int]]]:
        """
        Extracts metadata from the result of Azure Document Intelligence OCR.

        :param file_path: Path of the file processed.
        :param result_ocr: The result from Azure Document Intelligence OCR. If not provided, the function will raise a ValueError.
        :return: Dictionary with metadata.
        """
        try:
            result_ocr = result_ocr or self.result_ocr
            if result_ocr is None:
                warnings.warn("No OCR result available.")

            section_headings = [
                paragraph["content"]
                for paragraph in result_ocr.get("paragraphs", [])
                if paragraph.get("role") == "sectionHeading"
            ]

            # Check if section_headings is empty
            if not section_headings:
                warnings.warn("extracting metadta...section_headings is empty")

            # Extracting available metadata
            metadata = {
                "source_url": file_path,
                "apiVersion": result_ocr.get("apiVersion"),
                "modelId": result_ocr.get("modelId"),
                "contentFormat": result_ocr.get("contentFormat"),
                "sectionHeading": section_headings,
                # Add other properties as needed
            }

            # Check if metadata is empty
            if not any(metadata.values()):
                warnings.warn("Metadata is empty")

            return metadata
        except Exception as e:
            logger.error(f"Failed to extract metadata for file {file_path}: {e}")
            return {}
