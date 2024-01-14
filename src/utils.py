import re
from typing import Optional, Tuple


def get_container_and_blob_name_from_url(blob_url: str) -> tuple:
    """
    Retrieves the container name and the blob name from a blob URL.

    The container name is always the part of the URL before the last '/'.
    The blob name is always the part of the URL after the last '/'.

    :param blob_url: The blob URL.
    :return: A tuple containing the container name and the blob name.
    """
    # Split the URL by '/'
    parts = blob_url.split("/")

    # The container name is the second to last part
    container_name = parts[-2]

    # The blob name is the last part
    blob_name = parts[-1]

    return container_name, blob_name


def get_sharepoint_details(
    sharepoint_url: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extracts the domain, site name, and folder path from a SharePoint URL.

    :param sharepoint_url: The SharePoint URL.
    :return: A tuple containing the domain, site name, and folder path. If the URL does not match
    the expected format, None is returned for each element.
    """
    # Regular expression to match the SharePoint URL pattern
    pattern = r"https://([^/]+)/sites/([^/]+)(.*)"

    match = re.match(pattern, sharepoint_url)

    if match:
        domain = match.group(1)
        site_name = match.group(2)
        folder_path = match.group(3)
        return domain, site_name, folder_path
    else:
        return None, None, None
