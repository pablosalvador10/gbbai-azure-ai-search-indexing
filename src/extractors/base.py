from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any, Dict


class DataExtractor(ABC):
    """
    Abstract base class for data extraction.

    This class defines the interface for data extraction. It includes methods for extracting content,
    metadata and formatting it. Subclasses should implement these methods to provide specific
    data extraction functionality.
    """

    @abstractmethod
    def extract_metadata(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Abstract method to extract specific information from the file data.
        """
        pass

    @abstractmethod
    def extract_content(self, file_path: str) -> BytesIO:
        """
        Retrieve the content of a file as bytes from a specific site drive.

        :param site_id: The site ID in Microsoft Graph.
        :param drive_id: The drive ID in Microsoft Graph.
        :param folder_path: Path to the folder within the drive, can include subfolders.
        :param file_name: The name of the file.
        :param specific_file: Specific file name, if different from file_name.
        :param access_token: The access token for Microsoft Graph API authentication.
        :return: Bytes content of the file or None if there's an error.
        """
        pass
