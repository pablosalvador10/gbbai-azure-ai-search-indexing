from typing import Dict, List, Optional, Union

from langchain.docstore.document import Document
from langchain.text_splitter import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)

from utils.ml_logging import get_logger

# Initialize logging
logger = get_logger()


def get_splitter(
    use_recursive_splitter: bool,
    chunk_size: int = 512,
    chunk_overlap: int = 128,
    recursive_separators: Optional[List[str]] = None,
    char_separator: Optional[str] = "\n\n",
    keep_separator: bool = True,
    is_separator_regex: bool = False,
    **kwargs,
) -> Union[RecursiveCharacterTextSplitter, CharacterTextSplitter]:
    """
    Returns an instance of a text splitter based on the provided parameters.

    :param use_recursive_splitter: Boolean flag to choose between recursive or non-recursive splitter.
    :param chunk_size: The number of characters in each text chunk.
    :param chunk_overlap: The number of characters to overlap between chunks.
    :param recursive_separators: List of strings or regex patterns to use as separators for splitting with RecursiveCharacterTextSplitter.
    :param char_separator: String or regex pattern to use as a separator for splitting with CharacterTextSplitter.
    :param keep_separator: Whether to keep the separators in the resulting chunks.
    :param is_separator_regex: Treat the separators as regex patterns.
    :param kwargs: Additional keyword arguments to pass to the splitter class.
    :return: An instance of either RecursiveCharacterTextSplitter or CharacterTextSplitter.
    """
    try:
        if use_recursive_splitter:
            return RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=recursive_separators,
                keep_separator=keep_separator,
                is_separator_regex=is_separator_regex,
                **kwargs,
            )
        else:
            return CharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separator=char_separator,
                is_separator_regex=is_separator_regex,
                **kwargs,
            )
    except Exception as e:
        logger.error(f"Failed to get splitter: {e}")
        raise


def split_documents_in_chunks_from_documents(
    documents: List[Document],
    chunk_size: Optional[int] = 1000,
    chunk_overlap: Optional[int] = 200,
    recursive_separators: Optional[List[str]] = None,
    char_separator: Optional[str] = "\n\n",
    keep_separator: bool = True,
    is_separator_regex: bool = False,
    use_recursive_splitter: bool = True,
    **kwargs,
) -> List[Document]:
    """
    Splits text from a list of Document objects into manageable chunks.
    The method can use either RecursiveCharacterTextSplitter or CharacterTextSplitter based on the flag.

    :param documents: List of Document objects to split.
    :param chunk_size: The number of characters in each text chunk. Defaults to 1000.
    :param chunk_overlap: The number of characters to overlap between chunks. Defaults to 200.
    :param recursive_separators: List of strings or regex patterns to use as separators for splitting with RecursiveCharacterTextSplitter.
    :param char_separator: String or regex pattern to use as a separator for splitting with CharacterTextSplitter.
    :param keep_separator: Whether to keep the separators in the resulting chunks. Defaults to True.
    :param is_separator_regex: Treat the separators as regex patterns. Defaults to False.
    :param use_recursive_splitter: Boolean flag to choose between recursive or non-recursive splitter. Defaults to False.
    :return: A list of text chunks.
    """
    try:
        text_splitter = get_splitter(
            use_recursive_splitter,
            chunk_size,
            chunk_overlap,
            recursive_separators,
            char_separator,
            keep_separator,
            is_separator_regex,
            **kwargs,
        )
        logger.info(f"Obtained splitter of type: {type(text_splitter).__name__}")

        chunks = text_splitter.split_documents(documents)
        logger.info(f"Number of chunks obtained: {len(chunks)}")

        return chunks
    except Exception as e:
        logger.error(f"Error in splitting text: {e}")
        raise


def split_documents_in_chunks_from_text(
    text: str,
    metadata: Dict[str, str],
    chunk_size: Optional[int] = 1000,
    chunk_overlap: Optional[int] = 200,
    **kwargs,
) -> List[Document]:
    """
    Splits a given text into chunks and creates Document objects from each chunk.

    :param text: The text to be split.
    :param metadata: A dictionary containing metadata for each Document.
    :param chunk_size: The number of characters in each text chunk. Defaults to 1000.
    :param chunk_overlap: The number of characters to overlap between chunks. Defaults to 200.
    :return: A list of Document objects, each with associated metadata.
    """
    try:
        text_splitter = get_splitter(
            use_recursive_splitter=False,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs,
        )
        logger.info(f"Obtained splitter of type: {type(text_splitter).__name__}")

        docs = [
            Document(page_content=chunk, metadata=metadata)
            for chunk in text_splitter.split_text(text)
        ]
        logger.info(f"Number of chunks obtained: {len(docs)}")

        return docs
    except Exception as e:
        logger.error(f"Error in splitting text: {e}")
        raise
