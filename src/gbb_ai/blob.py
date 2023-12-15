import io
import os
import json
import pickle
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from typing import Any, Literal, Optional

class AzureBlobManager:
    """
    Class for managing interactions with Azure Blob Storage. It provides functionalities
    to read and write data to blobs, especially focused on handling Pandas DataFrames.

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
        self.credential = DefaultAzureCredential()
        storage_url = os.environ["AZURE_STORAGE_BLOB_URL"]
        self.service_client = BlobServiceClient(account_url=storage_url, credential=self.credential)
        self.container_client = self.service_client.get_container_client(container_name)

    def load_object(self, blob_name: str, file_format: Optional[Literal["csv", "json", "pickle", "parquet"]] = None) -> Any:
        """
        Loads an object from Azure Blob Storage. The object can be a CSV, JSON, Pickle file, or a Parquet file.

        Args:
            blob_name (str): The name of the blob to read from.
            file_format (Optional[Literal["csv", "json", "pickle", "parquet"]]): The format of the file to read.
                If not specified, it will be inferred from the file extension.

        Returns:
            Any: The object read from the blob, typically a Pandas DataFrame.
        
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
        else:
            raise ValueError("Unsupported file format")

    def write_object(self, obj: Any, blob_name: str, file_format: Literal["csv", "json", "pickle", "parquet"]) -> None:
        """
        Writes an object to Azure Blob Storage. Supports writing CSV, JSON, Pickle files, and Parquet files.

        Args:
            obj (Any): The object to write, typically a Pandas DataFrame.
            blob_name (str): The name of the blob to write to.
            file_format (Literal["csv", "json", "pickle", "parquet"]): The format of the file to write.

        Raises:
            ValueError: If the file format is unsupported or the object is not a Pandas DataFrame when expected.
        """
        blob_client = self.container_client.get_blob_client(blob_name)

        if file_format == "csv":
            if not isinstance(obj, pd.DataFrame):
                raise ValueError("Object must be a Pandas DataFrame for CSV format")
            content = obj.to_csv(index=False)

        elif file_format == "json":
            content = json.dumps(obj)

        elif file_format == "pickle":
            content = pickle.dumps(obj)

        elif file_format == "parquet":
            if not isinstance(obj, pd.DataFrame):
                raise ValueError("Object must be a Pandas DataFrame for Parquet format")
            buffer = io.BytesIO()
            obj.to_parquet(buffer)
            content = buffer.getvalue()

        else:
            raise ValueError("Unsupported file format")

        blob_client.upload_blob(content, overwrite=True)