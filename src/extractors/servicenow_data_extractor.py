import os
from functools import wraps
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

# load logging
from utils.ml_logging import get_logger

logger = get_logger()


def headers_replace(f):
    """
    Decorator function to replace headers in the HTTP request.

    This function sets the 'Accept' and 'Content-Type' headers to 'application/json'.
    If an API token is provided, it sets the 'Authorization' header to 'Bearer {api_token}'.
    If a username and password are provided, it sets the session authentication to these values.
    If additional headers are provided in the kwargs, it merges these with the default headers.
    """

    @wraps(f)
    def decorated_function(self, *args, **kwargs):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        elif self.user and self.password:
            self.session.auth = (self.user, self.password)

        if "headers" in kwargs:
            headers = {**headers, **kwargs["headers"]}

        kwargs["headers"] = headers

        return f(self, *args, **kwargs)

    return decorated_function


class ServiceNowDataExtractor:
    """
    Class for extracting data from the ServiceNow API.
    """

    def __init__(self, instance_url: Optional[str] = None):
        """
        Initializes the ServiceNowDataExtractor with a ServiceNow instance URL.

        If an instance URL is not provided, the method uses the URL from the environment variable.

        Raises:
            EnvironmentError: If the ServiceNow username or password is not found in environment variables.
        """
        load_dotenv()
        self.user = os.getenv("SERVICENOW_USER")
        self.password = os.getenv("SERVICENOW_PASSWORD")
        self.api_token = os.getenv("SERVICENOW_API_TOKEN")

        if not instance_url:
            self.instance_url = os.getenv("SERVICENOW_URL")
        else:
            self.instance_url = instance_url

        if not (self.api_token or (self.user and self.password)):
            raise EnvironmentError(
                "Authentication credentials not found in environment variables."
            )

        self.base_url = f"{self.instance_url}/api/now/"
        self.session = requests.Session()

        if self.api_token:
            self.session.headers.update({"Authorization": f"Bearer {self.api_token}"})
        else:
            self.session.auth = (self.user, self.password)

        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

        # Test connection
        try:
            response = self.session.get(f"{self.base_url}table/incident")
            response.raise_for_status()
            logger.info(
                f"Successfully connected to ServiceNow instance: {self.instance_url}"
            )
        except Exception as e:
            logger.error(f"Error initializing ServiceNowDataExtractor: {e}")
            raise

    @headers_replace
    def __http_request(
        self,
        method: str,
        path: str,
        headers: dict = None,
        data: dict = None,
        params: dict = None,
    ):
        try:
            url = f"{self.base_url}{path}"
            prepared_request = self.session.prepare_request(
                requests.Request(method, url, headers=headers, json=data, params=params)
            )
            logger.info(f"Sending {method} request to {prepared_request.url}")
            response = self.session.send(prepared_request)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request error: {e}")
            return {}

    def get_records_from_table(
        self, table: str, query_params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieves records from a specific table in the ServiceNow instance.

        :param table: Name of the table to retrieve records from.
        :param query_params: Optional dictionary of query parameters to filter the records.
        :return: A dictionary containing the retrieved records, or an empty dictionary if no records are found.
        """
        return self.__http_request("GET", f"table/{table}", params=query_params)

    def get_incident(self, incident_id: str) -> Dict[str, Any]:
        """
        Retrieves a specific incident by its ID from the ServiceNow instance.

        :param incident_id: ID of the incident to retrieve.
        :return: A dictionary containing the incident record, or an empty dictionary if the incident ID is not found.
        """
        return self.get_records_from_table("incident", {"number": incident_id})

    def update_incident(
        self, incident_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Updates a specific incident in the ServiceNow instance.

        :param incident_id: ID of the incident to update.
        :param update_data: Dictionary of data to update the incident with.
        :return: A dictionary containing the updated incident record, or an empty dictionary if the PUT request fails.
        """
        return self.__http_request(
            "PUT", f"table/incident/{incident_id}", data=update_data
        )

    def create_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new incident in the ServiceNow instance.

        :param incident_data: Dictionary of data to create the incident with.
        :return: A dictionary containing the created incident record, or an empty dictionary if the POST request fails.
        """
        response = self.__http_request("POST", "table/incident", data=incident_data)
        if response:
            incident_number = response.get("result", {}).get("number", "")
            logger.info(f"Incident created with number: {incident_number}")
        return response

    def get_request(self, request_id: str) -> Dict[str, Any]:
        """
        Retrieves a specific request by its ID from the ServiceNow instance.

        :param request_id: ID of the request to retrieve.
        :return: A dictionary containing the request record, or an empty dictionary if the request ID is not found.
        """
        return self.get_records_from_table("request", {"number": request_id})

    def update_request(
        self, request_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Updates a specific request in the ServiceNow instance.

        :param request_id: ID of the request to update.
        :param update_data: Dictionary of data to update the request with.
        :return: A dictionary containing the updated request record, or an empty dictionary if the PUT request fails.
        """
        return self.__http_request(
            "PUT", f"table/request/{request_id}", data=update_data
        )

    def create_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new request in the ServiceNow instance.

        :param request_data: Dictionary of data to create the request with.
        :return: A dictionary containing the created request record, or an empty dictionary if the POST request fails.
        """
        response = self.__http_request("POST", "table/request", data=request_data)
        if response:
            request_number = response.get("result", {}).get("number", "")
            logger.info(f"Request created with number: {request_number}")
        return response

    def extract_metadata(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Abstract method to extract specific information from the file data.
        """
        pass

    def format_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Abstract method to format and return file metadata.
        """
        pass

    def extract_content(self, file_path: str) -> bytes:
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
