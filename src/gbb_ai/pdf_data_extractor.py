from typing import List, Tuple, Optional
import os
from PyPDF2 import PdfReader
import PyPDF2
import io
from azure.ai.formrecognizer import DocumentAnalysisClient, AnalyzedDocument
from azure.core.credentials import AzureKeyCredential


from dotenv import load_dotenv

# load logging
from utils.ml_logging import get_logger

logger = get_logger()


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> Optional[str]:
    """
    Extracts text from a PDF file provided as a bytes object.

    :param pdf_bytes: Bytes object containing the PDF file data.
    :return: Extracted text from the PDF as a string, or None if extraction fails.
    """
    try:
        with io.BytesIO(pdf_bytes) as pdf_stream:
            pdf_reader = PyPDF2.PdfReader (pdf_stream)
            text = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text.append(page.extract_text())

            extracted_text = '\n'.join(text)
            logger.info("Text extraction from PDF bytes was successful.")
            return extracted_text
    except Exception as e:
        logger.error(f"An unexpected error occurred during PDF text extraction: {e}")

    return None


class PDFHelper:
    """This class facilitates the processing of PDF files.
    It supports loading configuration from environment variables and provides methods for PDF text extraction.
    """

    def __init__(
        self,
        ocr_azure_endpoint: Optional[str] = None,
        ocr_azure_key: Optional[str] = None
    ):
        """
        Initialize the PDFHelper class with optional environment variables for Azure services.

        :param azure_endpoint: Azure Form Recognizer endpoint.
        :param azure_key: Azure Form Recognizer API key.
        """
        self.ocr_azure_endpoint = ocr_azure_endpoint
        self.ocr_azure_key = ocr_azure_key

    def load_environment_variables_from_env_file(self):
        """
        Loads required environment variables for Azure services from a .env file.

        This method should be called explicitly if environment variables are to be loaded from a .env file.
        """
        load_dotenv()

        self.ocr_azure_endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
        self.ocr_azure_key = os.getenv("AZURE_FORM_RECOGNIZER_KEY")

        # Check for any missing required environment variables
        missing_vars = [
            var_name
            for var_name, var in [
                ("AZURE_FORM_RECOGNIZER_ENDPOINT", self.ocr_azure_endpoint),
                ("AZURE_FORM_RECOGNIZER_KEY", self.ocr_azure_key),
            ]
            if not var
        ]

        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        # Log the success of loading each environment variable
        loaded_vars = [
            var_name
            for var_name in ["AZURE_FORM_RECOGNIZER_ENDPOINT", "AZURE_FORM_RECOGNIZER_KEY"]
            if var_name not in missing_vars
        ]
        if loaded_vars:
            logger.info(
                f"Successfully loaded environment variables: {', '.join(loaded_vars)}"
            )




# def extract_text_from_pdf(
#     file_path: str,
#     use_azure_recognizer: bool = False,
#     azure_endpoint: Optional[str] = None,
#     azure_key: Optional[str] = None,
#     azure_model: str = "prebuilt-document",
#     is_url: bool = False,
#     verbose: bool = False
# ) -> List[Tuple[int, int, str]]:
#     """
#     Extracts text from a PDF file using either PyPDF2 or Azure Document Intelligence SDK.

#     :param file_path: Path to the PDF file or URL if from_url is True.
#     :param form_recognizer: Whether to use Azure Document Intelligence SDK for extraction.
#     :param formrecognizer_endpoint: Azure Form Recognizer endpoint.
#     :param formrecognizer_key: Azure Form Recognizer API key.
#     :param model: Model ID for the Azure Form Recognizer.
#     :param from_url: Indicates if file_path is a URL to a PDF.
#     :param verbose: If True, prints additional information during processing.
#     :return: A list of tuples, each containing (page number, offset, extracted text).
#     """
#     page_map = []

#     if not form_recognizer:
#         if verbose:
#             print("Extracting text using PyPDF2")
#         reader = PdfReader(file_path)
#         pages = reader.pages
#         offset = 0
#         for page_num, page in enumerate(pages):
#             page_text = page.extract_text() or ""
#             page_map.append((page_num, offset, page_text))
#             offset += len(page_text)
#     else:
#         if verbose:
#             print("Extracting text using Azure Document Intelligence")
#         credential = AzureKeyCredential(formrecognizer_key or os.environ["FORM_RECOGNIZER_KEY"])
#         client = DocumentAnalysisClient(endpoint=formrecognizer_endpoint or os.environ["FORM_RECOGNIZER_ENDPOINT"], credential=credential)

#         poller = client.begin_analyze_document(model, document=open(file_path, "rb")) if not from_url else client.begin_analyze_document_from_url(model, document_url=file_path)
#         form_recognizer_results = poller.result()

#         # Process form recognizer results
#         page_map = process_form_recognizer_results(form_recognizer_results)

#     return page_map 

# def process_form_recognizer_results(results: AnalyzedDocument) -> List[Tuple[int, int, str]]:
#     """
#     Processes the results from Azure Form Recognizer to extract text.

#     :param results: The analyzed document result from Azure Form Recognizer.
#     :return: A list of tuples with extracted text and its metadata.
#     """
#     # Function implementation remains the same
#     # ...
#     page_map = []
#     offset = 0

#     for page_num, page in enumerate(results.pages):
#         # Additional processing can be added here
#         page_text = extract_text_from_page(page)
#         page_map.append((page_num, offset, page_text))
#         offset += len(page_text)

#     return page_map

# def extract_text_from_page(page: AnalyzedDocument) -> str:
#     """
#     Extracts text from a single page of the Azure Form Recognizer results.

#     :param page: A page from the Azure Form Recognizer results.
#     :return: Extracted text from the page.
#     """
#     # Function implementation remains the same
#     # ...
#     return " ".join([line.content for line in page.lines])

# def extract_text_from_pdf(
#     file_path: str,
#     use_azure_recognizer: bool = False,
#     azure_endpoint: Optional[str] = None,
#     azure_key: Optional[str] = None,
#     azure_model: str = "prebuilt-document",
#     is_url: bool = False,
#     verbose: bool = False
# ) -> List[Tuple[int, int, str]]:
#     """
#     Extracts text from a PDF file using either PyPDF2 or Azure Document Intelligence SDK.

#     :param files: A list of file paths or URLs to PDF files.
#     :param form_recognizer: Whether to use Azure Document Intelligence SDK for extraction.
#     :param verbose: If True, prints additional information during processing.
#     :param formrecognizer_endpoint: Azure Form Recognizer endpoint.
#     :param formrecognizer_key: Azure Form Recognizer API key.
#     :return: A tuple of two lists: extracted texts and corresponding source information.
#     """
#     # Function implementation remains the same
#     # ...
#     """Extracts text from a list of PDF files."""
#     text_list = []
#     sources_list = []

#     for file_path in files:
#         page_map = parse_pdf(file_path, form_recognizer=form_recognizer, verbose=verbose, formrecognizer_endpoint=formrecognizer_endpoint, formrecognizer_key=formrecognizer_key)
#         for page_num, (_, _, page_text) in enumerate(page_map):
#             text_list.append(page_text)
#             sources_list.append(f"{os.path.basename(file_path)}_page_{page_num + 1}")

#     return text_list, sources_list