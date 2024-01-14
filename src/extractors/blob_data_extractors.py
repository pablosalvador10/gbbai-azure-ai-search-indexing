import os
import tempfile
from io import BytesIO
from typing import List, Optional

from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

from utils.ml_logging import get_logger

# Initialize logger
logger = get_logger()


class AzureBlobDataExtractor:
    """
    Class for managing interactions with Azure Blob Storage. It provides functionalities
    to read and write data to blobs, especially focused on handling various file formats.

    Attributes:
        container_name (str): Name of the Azure Blob Storage container.
        service_client (BlobServiceClient): Azure Blob Service Client.
        container_client: Azure Container Client specific to the container.
    """

    def __init__(self, container_name: Optional[str] = None):
        """
        Initialize the AzureBlobManager with a container name.

        Args:
            container_name (str, optional): Name of the Azure Blob Storage container. Defaults to None.
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
            self.container_name = container_name
            self.blob_service_client = BlobServiceClient.from_connection_string(
                connect_str
            )
            if container_name:
                self.container_client = self.blob_service_client.get_container_client(
                    container_name
                )
        except Exception as e:
            logger.error(f"Error initializing AzureBlobManager: {e}")
            raise

    def change_container(self, new_container_name: str):
        """
        Changes the Azure Blob Storage container.

        Args:
            new_container_name (str): The name of the new container.
        """
        self.container_name = new_container_name
        self.container_client = self.blob_service_client.get_container_client(
            new_container_name
        )
        logger.info(f"Container changed to {new_container_name}")

    def download_blob_files(self, filenames: List[str]) -> List[BytesIO]:
        """
        Downloads blobs from a container.

        :param filenames: List of filenames to be downloaded from the blob.
        :return: List of BytesIO objects representing the downloaded blobs.
        """
        blob_data = []
        for filename in filenames:
            try:
                blob_client = self.blob_service_client.get_blob_client(filename)
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
