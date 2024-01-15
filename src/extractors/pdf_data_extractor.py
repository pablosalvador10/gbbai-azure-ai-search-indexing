import os
from typing import List, Optional, Union

from langchain.docstore.document import Document
from langchain.document_loaders import PyPDFLoader

from src.extractors.utils import get_container_and_blob_name_from_url
from src.loaders.base import AzureDocumentLoader

# load logging
from utils.ml_logging import get_logger

logger = get_logger()


def read_and_load(
    pdf_path: Optional[str] = None, pdf_url: Optional[str] = None, **kwargs
) -> Union[Document, List[Document]]:
    """
    Reads and loads a single PDF file from a given local path or a URL from Azure Blob Storage.

    This function checks if a local path or a URL is provided.
    If a local path is provided, it reads the file, loads its content, and returns a Document object.
    If a URL is provided, it checks if it's a blob URL. If it is, it downloads the file from Azure Blob Storage,
    reads it, loads its content, and returns a Document object.
    If the URL does not contain "blob.core.windows.net", it treats it as a local file path and follows
    the same logic as if a local path was provided.

    :param pdf_path: Path to the local PDF file.
    :param pdf_url: URL of the PDF file in Azure Blob Storage or a local file path.
    :return: A Document object containing the content of the PDF file.
    """
    if pdf_path is None and pdf_url is None:
        raise ValueError("Either 'pdf_path' or 'pdf_url' must be provided.")

    if pdf_path:
        # Convert relative path to absolute path
        pdf_path = os.path.abspath(pdf_path)

        logger.info(f"Reading PDF file from {pdf_path}.")

        if pdf_path.endswith(".pdf"):
            loader = PyPDFLoader(pdf_path, **kwargs)
            document = loader.load()
            return document
        else:
            raise ValueError("Invalid path. Path should be a .pdf file.")
    elif pdf_url:
        if "blob.core.windows.net" in pdf_url:
            logger.info(f"Downloading and reading PDF file from {pdf_url}.")
            container_name, file_name = get_container_and_blob_name_from_url(pdf_url)
            loader = AzureDocumentLoader(container_name=container_name)
            documents = loader.load_files_from_blob(filenames=[file_name], **kwargs)
            return documents
        else:
            logger.info(f"Reading PDF file from {pdf_url}.")

            if pdf_url.endswith(".pdf"):
                loader = PyPDFLoader(pdf_url, **kwargs)
                document = loader.load()
                return document
            else:
                raise ValueError("Invalid path. Path should be a .pdf file.")
    else:
        raise ValueError("Either a local path or a URL must be provided.")
