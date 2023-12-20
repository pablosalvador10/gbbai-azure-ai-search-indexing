import io
import os
import json
import pickle
import pandas as pd
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from typing import Any, Literal, Optional
from dotenv import load_dotenv
from docx import Document
import PyPDF2

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
        load_dotenv()
        connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if connect_str is None:
            raise EnvironmentError("AZURE_STORAGE_CONNECTION_STRING not found in environment variables.")
        self.service_client = BlobServiceClient.from_connection_string(connect_str)
        self.container_client = self.service_client.get_container_client(container_name)

    def load_object(self, blob_name: str, file_format: Optional[Literal["csv", "json", "pickle", "parquet", "docx", "pdf", "txt"]] = None) -> Any:
        """
        Loads an object from Azure Blob Storage. The object can be a CSV, JSON, Pickle, Parquet, DOCX, PDF, or a plain text file.

        Args:
            blob_name (str): The name of the blob to read from.
            file_format (Optional[Literal["csv", "json", "pickle", "parquet", "docx", "pdf", "txt"]]): The format of the file to read.
                If not specified, it will be inferred from the file extension.

        Returns:
            Any: The object read from the blob, typically a Pandas DataFrame for structured data files, or a string for DOCX, PDF, and text files.
        
        Raises:
            ValueError: If the file format is unsupported or not recognized.
        """
        blob_client = self.container_client.get_blob_client(blob_name)
        downloader = blob_client.download_blob()
        content = downloader.readall()

        if file_format in ["csv", "parquet"]:
            return pd.read_csv(io.StringIO(content.decode())) if file_format == "csv" else pd.read_parquet(io.BytesIO(content))
        elif file_format in ["json", "pickle"]:
            return json.loads(content) if file_format == "json" else pickle.loads(content)
        elif file_format == "docx":
            doc = Document(io.BytesIO(content))
            return '\n'.join([para.text for para in doc.paragraphs])
        elif file_format == "pdf":
            pdf_reader = PyPDF2.PdfFileReader(io.BytesIO(content))
            return '\n'.join([pdf_reader.getPage(i).extractText() for i in range(pdf_reader.numPages)])
        elif file_format == "txt":
            return content.decode()
        else:
            raise ValueError("Unsupported file format")
