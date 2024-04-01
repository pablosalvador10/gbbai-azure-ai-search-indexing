"""This class manages interactions with Azure Blob Storage, providing functionalities to read, write,
 and extract data and metadata from blobs in various file formats."""
import os
import tempfile
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Dict, List, Literal, Optional, Union

import pandas as pd
from azure.storage.blob import BlobServiceClient
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

from src.extractors.base import DataExtractor
from src.extractors.utils import get_container_and_blob_name_from_url
from utils.ml_logging import get_logger

# Initialize logger
logger = get_logger()


class AzureBlobDataExtractor(DataExtractor):
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

    def extract_content(self, file_path: str) -> bytes:
        """
        Downloads blobs from a container.

        :param filenames: List of filenames to be downloaded from the blob.
        :return: List of BytesIO objects representing the downloaded blobs.
        """
        (
            container_name,
            file_name,
        ) = get_container_and_blob_name_from_url(file_path)
        try:
            blob_data = (
                self.blob_service_client.get_blob_client(
                    container=container_name, blob=file_name
                )
                .download_blob()
                .readall()
            )
            logger.info(f"Successfully downloaded blob file {file_name}")
        except Exception as e:
            logger.error(f"Failed to download blob file {file_name}: {e}")
        return blob_data

    def extract_metadata(self, blob_url: str) -> Dict[str, Optional[Union[str, int]]]:
        """
        Extracts metadata from a blob in Azure Blob Storage.

        :param blob_url: URL of the blob.
        :return: Dictionary with metadata.
        """
        container_name, blob_name = get_container_and_blob_name_from_url(blob_url)
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )
            blob_properties = blob_client.get_blob_properties()

            # Extracting available metadata
            return {
                "source_url": blob_url,
                "name": blob_name,
                "size": blob_properties.size,
                "content_type": blob_properties.content_settings.content_type,
                "last_modified": blob_properties.last_modified,
                # Add other properties as needed
            }
        except Exception as e:
            logger.error(f"Failed to extract metadata for blob {blob_name}: {e}")
            return {}

    def format_metadata(self, metadata: Dict) -> Dict:
        """
        Format and return file metadata.

        :param metadata: Dictionary of file metadata.
        :param file_name: Name of the file.
        :param users_by_role: Dictionary of users grouped by their role.
        :return: Formatted metadata as a dictionary.
        """
        formatted_metadata = {
            "source": metadata.get("url"),
            "name": metadata.get("blob_name"),
            "size": metadata.get("size"),
            "content_type": metadata.get("content_type"),
            "last_modified": metadata.get("last_modified").isoformat()
            if metadata.get("last_modified")
            else None,
        }
        return formatted_metadata

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

    def list_updated_files(
        self,
        container_name: Optional[str] = None,
        updated_since: Optional[int] = None,
        time_unit: Optional[
            Literal["years", "months", "days", "hours", "minutes", "seconds"]
        ] = None,
    ) -> list[str]:
        """
        Lists files in the blob container that have been updated since a specified time.

        :param container_name: Name of the blob container. If not provided, uses the container name from the instance.
        :param updated_since: Number of time units (years, months, days, hours, minutes, seconds) since which to check for updates. If not provided, returns all files. Time is in UTC.
        :param time_unit: Time unit to use when calculating the time since which to check for updates. Default is None.
        :return: List of filenames of updated files.
        """
        # Get the blob container
        container_name = (
            container_name if container_name is not None else self.container_name
        )
        container_client = self.blob_service_client.get_container_client(
            container=container_name
        )

        if updated_since is not None and time_unit is not None:
            if time_unit == "years":
                updated_since_datetime = datetime.now(timezone.utc) - relativedelta(
                    years=updated_since
                )
            elif time_unit == "months":
                updated_since_datetime = datetime.now(timezone.utc) - relativedelta(
                    months=updated_since
                )
            elif time_unit == "days":
                updated_since_datetime = datetime.now(timezone.utc) - timedelta(
                    days=updated_since
                )
            elif time_unit == "hours":
                updated_since_datetime = datetime.now(timezone.utc) - timedelta(
                    hours=updated_since
                )
            elif time_unit == "minutes":
                updated_since_datetime = datetime.now(timezone.utc) - timedelta(
                    minutes=updated_since
                )
            elif time_unit == "seconds":
                updated_since_datetime = datetime.now(timezone.utc) - timedelta(
                    seconds=updated_since
                )
            else:
                raise ValueError(
                    "Invalid time_unit. Must be 'years', 'months', 'days', 'hours', 'minutes', or 'seconds'."
                )
        else:
            updated_since_datetime = datetime.min.replace(tzinfo=timezone.utc)

        # Get the blob container
        container_client = self.blob_service_client.get_container_client(container_name)

        # List all blobs in the container
        blob_list = container_client.list_blobs()

        updated_files = []
        for blob in blob_list:
            # Get the blob client
            blob_client = container_client.get_blob_client(blob.name)

            # Get the blob properties to check the last modified time
            blob_properties = blob_client.get_blob_properties()

            # Get the last modified time of the blob
            last_modified = blob_properties.last_modified.astimezone()

            # Check if the blob was updated after the specified date
            if last_modified > updated_since_datetime:
                # If updated, add the blob name to the list
                updated_files.append(blob_client.url)

        return updated_files

    def read_csv_from_blob(
        self, blob_name: str, container_name: Optional[str] = None, **kwargs
    ) -> pd.DataFrame:
        """
        Reads a CSV file from Azure Blob Storage and converts it into a pandas DataFrame.

        :param blob_name: The name of the blob (CSV file) in Azure Blob Storage.
        :param container_name: The name of the container in Azure Blob Storage.
                               If not provided, the default container name set in the class is used.
        :return: A pandas DataFrame containing the data from the CSV file.
        :raises ValueError: If both the container_name argument and default_container_name attribute are None.
        """
        if container_name is None:
            if self.container_name is None:
                raise ValueError(
                    "Container name must be provided either as an argument or as a default in the class."
                )
            else:
                container_name = self.container_name

        blob_client = self.blob_service_client.get_blob_client(
            container_name, blob_name
        )

        with BytesIO() as blob_io:
            blob_client.download_blob().readinto(blob_io)
            blob_io.seek(0)  # Go to the start of the stream
            df = pd.read_csv(blob_io, **kwargs)

        return df
