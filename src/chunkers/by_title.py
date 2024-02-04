import re
from typing import List

from langchain.docstore.document import Document

from src.chunkers.base import DocumentSplitter
from utils.ml_logging import get_logger

# Initialize logging
logger = get_logger()


class TitleDocumentSplitter(DocumentSplitter):

    """
    A document splitter that splits documents based on character count.
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    def split_text_by_headings(text: str, section_headings: List[str]) -> List[str]:
        """
        Splits text into chunks based on provided section headings.

        :param text: The text to be split.
        :param section_headings: A list of headings used to split the text.
        :return: List of text chunks.
        """
        pattern = "|".join("(?={})".format(re.escape(sec)) for sec in section_headings)
        chunks = re.split(pattern, text)

        logger.info(f"Section headings: {section_headings}")
        logger.info(f"Number of chunks: {len(chunks)}")

        return chunks

    def combine_chunks(
        self, chunks: List[str], min_length: int = 250, max_length: int = None
    ) -> List[str]:
        """
        Combines text chunks into larger chunks with a minimum and maximum number of tokens.
        """
        combined_chunks = []
        current_chunk = ""
        for i, chunk in enumerate(chunks):
            if (
                max_length is None
                or self.tokenizer.num_tokens_from_string(current_chunk + chunk)
                <= max_length
            ):
                current_chunk += chunk
            else:
                if self.tokenizer.num_tokens_from_string(current_chunk) >= min_length:
                    combined_chunks.append(current_chunk)
                current_chunk = chunk
            logger.info(f"Processed chunk {i+1} of {len(chunks)}")
        if (
            current_chunk
            and self.tokenizer.num_tokens_from_string(current_chunk) >= min_length
        ):
            combined_chunks.append(current_chunk)
        return combined_chunks

    def split_documents_in_chunks_from_documents(
        self,
        documents: List[Document],
        chunk_size: int = None,
        section_headings: List[str] = None,
    ) -> List[Document]:
        """
        Splits a list of Document objects into chunks.
        """
        chunked_documents = []
        for i, document in enumerate(documents):
            try:
                # Access page_content and metadata
                page_content = document.page_content
                metadata = document.metadata

                # If section_headings is not provided, use the section_headings from the metadata
                section_headings = section_headings or metadata.get(
                    "sectionHeading", []
                )

                # Check if section_headings is empty
                if not section_headings:
                    raise ValueError("section_headings is empty")

                # Apply logic
                splitted_chunks = self.split_text_by_headings(
                    page_content, section_headings
                )
                chunks = self.combine_chunks(
                    chunks=splitted_chunks, max_length=chunk_size
                )

                # Load results back into Document objects
                for chunk in chunks:
                    chunked_document = Document(page_content=chunk, metadata=metadata)
                    chunked_documents.append(chunked_document)

                logger.info(f"Processed document {i+1} of {len(documents)}")
            except ValueError as ve:
                logger.error(f"Failed to process document {i+1} due to error: {ve}")
            except Exception as e:
                logger.error(
                    f"Unexpected error occurred while processing document {i+1}: {e}"
                )
        return chunked_documents
