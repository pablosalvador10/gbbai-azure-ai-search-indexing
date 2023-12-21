from PyPDF2 import PdfFileReader
from dotenv import load_dotenv
import io

# load logging
from utils.ml_logging import get_logger

logger = get_logger()

class PDFHelper:
    """This class facilitates the processing of PDF files.
    It supports loading configuration from environment variables and provides methods for PDF text extraction.
    """

    def __init__(self):
        """
        Initialize the PDFHelper class.
        """
        logger.info("PDFHelper initialized.")

    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """
        Extracts text from a PDF file provided as a bytes object.

        :param pdf_bytes: Bytes object containing the PDF file data.
        :return: Extracted text from the PDF as a string, or None if extraction fails.
        """
        try:
            with io.BytesIO(pdf_bytes) as pdf_stream:
                pdf_reader = PdfFileReader(pdf_stream)
                text = []
                for page_num in range(pdf_reader.getNumPages()):
                    page = pdf_reader.getPage(page_num)
                    text.append(page.extractText())

                extracted_text = '\n'.join(text)
                logger.info("Text extraction from PDF bytes was successful.")
                return extracted_text
        except Exception as e:
            logger.error(f"An unexpected error occurred during PDF text extraction: {e}")
            return None

    def extract_metadata_from_pdf_bytes(self, pdf_bytes: bytes) -> dict:
        """
        Extracts metadata from a PDF file provided as a bytes object.

        :param pdf_bytes: Bytes object containing the PDF file data.
        :return: A dictionary containing the extracted metadata, or None if extraction fails.
        """
        try:
            with io.BytesIO(pdf_bytes) as pdf_stream:
                pdf = PdfFileReader(pdf_stream)
                information = pdf.getDocumentInfo()
                number_of_pages = pdf.getNumPages()

                metadata = {
                    "Author": information.author,
                    "Creator": information.creator,
                    "Producer": information.producer,
                    "Subject": information.subject,
                    "Title": information.title,
                    "Number of pages": number_of_pages
                }

                logger.info("Metadata extraction from PDF bytes was successful.")
                return metadata
        except Exception as e:
            logger.error(f"An unexpected error occurred during PDF metadata extraction: {e}")
            return None



    