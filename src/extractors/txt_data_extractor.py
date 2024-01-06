import io

from utils.ml_logging import get_logger

# Initialize logging
logger = get_logger()


class TextFileHelper:
    """
    This class facilitates the processing of text files.
    It provides methods for text file content extraction.
    """

    def __init__(self):
        """
        Initialize the TextFileHelper class.
        """
        logger.info("TextFileHelper initialized.")

    def extract_text_from_txt_bytes(self, txt_bytes: bytes) -> str:
        """
        Extracts text from a text file provided as a bytes object.

        :param txt_bytes: Bytes object containing the text file data.
        :return: Extracted text from the text file as a string, or an empty string if extraction fails.
        """
        try:
            with io.BytesIO(txt_bytes) as txt_stream:
                return self._extract_text_from_txt(txt_stream)
        except Exception as e:
            logger.error(f"An unexpected error occurred during text extraction: {e}")
            return ""

    def extract_text_from_txt_file(self, file_path: str) -> str:
        """
        Extracts text from a text file located at the given file path.

        :param file_path: Path to the text file.
        :return: Extracted text from the text file as a string, or None if extraction fails.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return self._extract_text_from_txt(file)
        except Exception as e:
            logger.error(
                f"An unexpected error occurred when opening the text file: {e}"
            )
            return ""

    def _extract_text_from_txt(self, file_stream) -> str:
        """
        Helper method to extract text from a text file stream.

        :param file_stream: File stream of the text file.
        :return: Extracted text from the text file as a string, or None if extraction fails.
        """
        try:
            text = file_stream.read()
            logger.info("Text extraction from text file was successful.")
            return text
        except Exception as e:
            logger.error(f"An unexpected error occurred during text extraction: {e}")
            return ""
