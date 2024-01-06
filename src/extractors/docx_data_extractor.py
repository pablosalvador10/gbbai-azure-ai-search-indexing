import io

from docx import Document

from utils.ml_logging import get_logger

# Initialize logging
logger = get_logger()


class DocxHelper:
    """
    This class facilitates the processing of DOCX files.
    It provides methods for DOCX text extraction.
    """

    def __init__(self):
        """
        Initialize the DocxHelper class.
        """
        logger.info("DocxHelper initialized.")

    def extract_text_from_docx_bytes(self, docx_bytes: bytes) -> str:
        """
        Extracts text from a DOCX file provided as a bytes object.

        :param docx_bytes: Bytes object containing the DOCX file data.
        :return: Extracted text from the DOCX as a string, or None if extraction fails.
        """
        try:
            with io.BytesIO(docx_bytes) as docx_stream:
                return self._extract_text_from_docx(docx_stream)
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during DOCX text extraction: {e}"
            )
            return ""

    def extract_text_from_docx_file(self, file_path: str) -> str:
        """
        Extracts text from a DOCX file located at the given file path.

        :param file_path: Path to the DOCX file.
        :return: Extracted text from the DOCX as a string, or None if extraction fails.
        """
        try:
            with open(file_path, "rb") as file:
                return self._extract_text_from_docx(file)
        except Exception as e:
            logger.error(
                f"An unexpected error occurred when opening the DOCX file: {e}"
            )
            return ""

    def _extract_text_from_docx(self, file_stream) -> str:
        """
        Helper method to extract text from a DOCX file stream.

        :param file_stream: File stream of the DOCX file.
        :return: Extracted text from the DOCX as a string, or None if extraction fails.
        """
        try:
            document = Document(file_stream)
            text = [paragraph.text for paragraph in document.paragraphs]

            extracted_text = "\n".join(text)
            logger.info("Text extraction from DOCX was successful.")
            return extracted_text
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during DOCX text extraction: {e}"
            )
            return ""
