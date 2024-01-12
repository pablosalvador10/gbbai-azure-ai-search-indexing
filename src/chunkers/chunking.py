from typing import Dict, List, Literal, Optional, Union

import tiktoken
from langchain.docstore.document import Document
from langchain.text_splitter import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    SpacyTextSplitter,
    TokenTextSplitter,
)

from src.settings import encoding_name_for_model
from utils.ml_logging import get_logger

# Initialize logging
logger = get_logger()

# initialize splitter type
SplitterType = Literal["recursive", "tiktoken", "spacy"]


def get_splitter(
    splitter_type: SplitterType = "recursive",
    use_encoder: bool = True,
    chunk_size: int = 512,
    chunk_overlap: int = 128,
    recursive_separators: Optional[List[str]] = None,
    char_separator: Optional[str] = "\n\n",
    keep_separator: bool = True,
    is_separator_regex: bool = False,
    model_name: Optional[str] = "gpt-4",
    **kwargs,
) -> Union[
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
    SpacyTextSplitter,
]:
    """
    Returns an instance of a text splitter based on the provided parameters.

    :param splitter_type: The type of splitter to use. Can be "recursive", "tiktoken", "spacy", or "character".
                          If not found, the character splitter will be selected. Defaults to "recursive".
    :param use_encoder: Boolean flag to choose whether to use an encoder for the splitter. Defaults to True.
    :param chunk_size: The number of characters in each text chunk. Defaults to 512.
    :param chunk_overlap: The number of characters to overlap between chunks. Defaults to 128.
    :param recursive_separators: List of strings or regex patterns to use as separators for splitting with RecursiveCharacterTextSplitter.
    :param char_separator: String or regex pattern to use as a separator for splitting with CharacterTextSplitter.
    :param keep_separator: Whether to keep the separators in the resulting chunks. Defaults to True.
    :param is_separator_regex: Treat the separators as regex patterns. Defaults to False.
    :param model_name: The name of the model to use for encoding, if use_encoder is True. Defaults to "gpt-4".
    :param kwargs: Additional keyword arguments to pass to the splitter class.
    :return: An instance of either RecursiveCharacterTextSplitter, TokenTextSplitter, SpacyTextSplitter, or CharacterTextSplitter.
    """
    try:
        logger.info(f"Creating a splitter of type: {splitter_type}")
        if splitter_type == "recursive":
            if use_encoder:
                if model_name is None:
                    raise ValueError(
                        "Model name must be provided. if use_encoder is True."
                    )
                encodername = encoding_name_for_model(model_name)
                logger.info(f"Using tiktoken encoder: {encodername}")
                return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                    encoding_name=encodername,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separators=recursive_separators,
                    keep_separator=keep_separator,
                    is_separator_regex=is_separator_regex,
                    **kwargs,
                )
            else:
                return RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separators=recursive_separators,
                    keep_separator=keep_separator,
                    is_separator_regex=is_separator_regex,
                    **kwargs,
                )
        elif splitter_type == "tiktoken":
            if model_name is None:
                raise ValueError("Model name must be provided. if use_encoder is True.")
            encodername = encoding_name_for_model(model_name)
            tiktoken_encoder = tiktoken.get_encoding(encodername)
            logger.info(f"Using tiktoken encoder: {encodername}")
            return TokenTextSplitter.from_tiktoken_encoder(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                encoder=tiktoken_encoder,
                **kwargs,
            )
        elif splitter_type == "spacy":
            # python -m spacy download en_core_web_sm
            logger.info("Using spacy NLP model: en_core_web_sm")
            return SpacyTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                pipeline="en_core_web_sm",
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
    splitter_type: SplitterType = "recursive",
    use_encoder: bool = True,
    chunk_size: int = 512,
    chunk_overlap: int = 128,
    recursive_separators: Optional[List[str]] = None,
    char_separator: Optional[str] = "\n\n",
    keep_separator: bool = True,
    is_separator_regex: bool = False,
    model_name: Optional[str] = "gpt-4",
    verbose: bool = False,
    **kwargs,
) -> List[Document]:
    """
    Splits text from a list of Document objects into manageable chunks. The method can use either
    RecursiveCharacterTextSplitter, TokenTextSplitter, SpacyTextSplitter, or CharacterTextSplitter based on the splitter_type.

    :param documents: List of Document objects to split.
    :param splitter_type: The type of splitter to use. Can be "recursive", "tiktoken", "spacy", or "character".
                        If not found, the character splitter will be selected. Defaults to "recursive".
    :param use_encoder: Boolean flag to choose whether to use an encoder for the splitter. Defaults to True.
    :param chunk_size: The number of characters in each text chunk. Defaults to 512.
    :param chunk_overlap: The number of characters to overlap between chunks. Defaults to 128.
    :param recursive_separators: List of strings or regex patterns to use as separators for splitting with RecursiveCharacterTextSplitter.
    :param char_separator: String or regex pattern to use as a separator for splitting with CharacterTextSplitter.
    :param keep_separator: Whether to keep the separators in the resulting chunks. Defaults to True.
    :param is_separator_regex: Treat the separators as regex patterns. Defaults to False.
    :param model_name: The name of the model to use for encoding, if use_encoder is True. Defaults to "gpt-4".
    :return: A list of text chunks.
    """
    try:
        text_splitter = get_splitter(
            splitter_type,
            use_encoder,
            chunk_size,
            chunk_overlap,
            recursive_separators,
            char_separator,
            keep_separator,
            is_separator_regex,
            model_name,
            **kwargs,
        )
        logger.info(f"Obtained splitter of type: {type(text_splitter).__name__}")

        chunks = text_splitter.split_documents(documents)
        logger.info(f"Number of chunks obtained: {len(chunks)}")

        if verbose:
            count_length_per_chunk(chunks, model_name)

        return chunks
    except Exception as e:
        logger.error(f"Error in splitting text: {e}")
        raise


def split_documents_in_chunks_from_text(
    text: str,
    metadata: Dict[str, str],
    splitter_type: SplitterType = "recursive",
    use_encoder: bool = True,
    chunk_size: int = 512,
    chunk_overlap: int = 128,
    recursive_separators: Optional[List[str]] = None,
    char_separator: Optional[str] = "\n\n",
    keep_separator: bool = True,
    is_separator_regex: bool = False,
    model_name: Optional[str] = "gpt-4",
    **kwargs,
) -> List[Document]:
    """
    Splits a given text into chunks and creates Document objects from each chunk. The method can use either
    RecursiveCharacterTextSplitter, TokenTextSplitter, SpacyTextSplitter, or CharacterTextSplitter based on the splitter_type.

    :param text: The text to be split.
    :param metadata: A dictionary containing metadata for each Document.
    :param splitter_type: The type of splitter to use. Can be "recursive", "tiktoken", "spacy", or "character".
                        If not found, the character splitter will be selected. Defaults to "recursive".
    :param use_encoder: Boolean flag to choose whether to use an encoder for the splitter. Defaults to True.
    :param chunk_size: The number of characters in each text chunk. Defaults to 512.
    :param chunk_overlap: The number of characters to overlap between chunks. Defaults to 128.
    :param recursive_separators: List of strings or regex patterns to use as separators for splitting with RecursiveCharacterTextSplitter.
    :param char_separator: String or regex pattern to use as a separator for splitting with CharacterTextSplitter.
    :param keep_separator: Whether to keep the separators in the resulting chunks. Defaults to True.
    :param is_separator_regex: Treat the separators as regex patterns. Defaults to False.
    :param model_name: The name of the model to use for encoding, if use_encoder is True. Defaults to "gpt-4".
    :return: A list of Document objects, each with associated metadata.
    """
    try:
        text_splitter = get_splitter(
            splitter_type,
            use_encoder,
            chunk_size,
            chunk_overlap,
            recursive_separators,
            char_separator,
            keep_separator,
            is_separator_regex,
            model_name,
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


def count_length_per_chunk(
    documents: List[Document], model_name: str = "gpt-4"
) -> None:
    """
    Counts and prints the length of the text in each chunk of each document.

    :param documents: List of Document objects to process.
    """
    # Initialize the tokenizer
    encodername = encoding_name_for_model(model_name)
    tokenizer = tiktoken.get_encoding(encodername)

    for idx_chunk, chunk in enumerate(documents):
        chunk_length = len(chunk.page_content)
        tokens = tokenizer.encode(chunk.page_content)
        token_count = len(tokens)
        print(
            f"Chunk Number: {idx_chunk+1}, Character Count: {chunk_length}, Token Count: {token_count}"
        )
