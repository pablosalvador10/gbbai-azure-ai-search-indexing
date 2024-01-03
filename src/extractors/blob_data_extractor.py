import io
import json
import os
import pickle
from typing import Any

import pandas as pd
from azure.storage.blob import BlobServiceClient
from docx import Document
from dotenv import load_dotenv

from src.extractors.pdf_data_extractor import PDFHelper
from utils.ml_logging import get_logger

logger = get_logger()
pdf_helper = PDFHelper()


class AzureBlobManager:
    """
    Class for managing interactions with Azure Blob Storage. It provides functionalities
    to read and write data to blobs, especially focused on handling various file formats.

    Attributes:
        container_name (str): Name of the Azure Blob Storage container.
        service_client (BlobServiceClient): Azure Blob Service Client.
        container_client: Azure Container Client specific to the container.
    """

    def __init__(self, container_name: str):
        """
        Initialize the AzureBlobManager with a container name.

        Args:
            container_name (str): Name of the Azure Blob Storage container.
        """
        try:
            load_dotenv()
            connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            if connect_str is None:
                logger.error(
                    "AZURE_STORAGE_CONNECTION_STRING not found in environment variables."
                )
                raise EnvironmentError(
                    "AZURE_STORAGE_CONNECTION_STRING not found in environment variables."
                )
            self.service_client = BlobServiceClient.from_connection_string(connect_str)
            self.container_client = self.service_client.get_container_client(
                container_name
            )
            logger.info(f"Initialized AzureBlobManager with container {container_name}")
        except Exception as e:
            logger.error(f"Error initializing AzureBlobManager: {e}")
            raise

    def change_container(self, new_container_name: str):
        """
        Changes the Azure Blob Storage container.

        Args:
            new_container_name (str): The name of the new container.
        """
        self.container_client = self.service_client.get_container_client(
            new_container_name
        )
        logger.info(f"Container changed to {new_container_name}")

    def load_object(self, file_name: str) -> Any:
        """
        Loads an object from Azure Blob Storage based on the file extension.
        Supported file formats are CSV, JSON, Pickle, Parquet, DOCX, PDF, and plain text.

        Args:
            file_name (str): The name of the file to read from.

        Returns:
            Any: The object read from the file, typically a Pandas DataFrame for structured data files,
                or a string for DOCX, PDF, and text files.

        Raises:
            ValueError: If the file format is unsupported or not recognized.
        """
        try:
            # Extract file format from the file name
            _, file_extension = os.path.splitext(file_name)
            file_format = file_extension.lstrip(".").lower()

            blob_client = self.container_client.get_blob_client(file_name)
            downloader = blob_client.download_blob()
            content = downloader.readall()
            if file_format == "csv":
                data = pd.read_csv(io.StringIO(content.decode()))
                logger.info(f"Successfully loaded CSV file {file_name}")
            elif file_format == "parquet":
                data = pd.read_parquet(io.BytesIO(content))
                logger.info(f"Successfully loaded Parquet file {file_name}")
            elif file_format == "json":
                data = json.loads(content)
                logger.info(f"Successfully loaded JSON file {file_name}")
            elif file_format == "pickle":
                data = pickle.loads(content)
                logger.info(f"Successfully loaded Pickle file {file_name}")
            elif file_format == "docx":
                doc = Document(io.BytesIO(content))
                data = "\n".join([para.text for para in doc.paragraphs])
                logger.info(f"Successfully loaded DOCX file {file_name}")
            elif file_format == "pdf":
                data = pdf_helper.extract_text_from_pdf_bytes(content)
                metadata = pdf_helper.extract_metadata_from_pdf_bytes(content)
                logger.info(f"Successfully loaded PDF file {metadata}")
            elif file_format == "txt":
                data = content.decode()
                logger.info(f"Successfully loaded TXT file {file_name}")
            else:
                logger.error(f"Unsupported file format: {file_format}")
                raise ValueError("Unsupported file format: " + file_format)

            return data
        except Exception as e:
            logger.error(f"Error loading object from blob: {e}")
            raise
