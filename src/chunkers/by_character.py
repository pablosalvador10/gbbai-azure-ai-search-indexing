from typing import List, Literal, Optional, Union

from langchain.docstore.document import Document
from langchain.text_splitter import (
    CharacterTextSplitter,
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
)

from src.aoai.settings import encoding_name_for_model
from src.chunkers.base import DocumentSplitter
from src.chunkers.utils import count_length_per_chunk
from utils.ml_logging import get_logger

# Initialize logging
logger = get_logger()


class CharacterDocumentSplitter(DocumentSplitter):
    """
    A document splitter that splits documents based on character count.
    """

    def __init__(self):
        super().__init__()

    def get_splitter(
        self,
        splitter_type: Literal[
            "by_character_recursive", "by_character_brute_force", "by_title_brute_force"
        ] = "by_character_recursive",
        use_encoder: bool = True,
        chunk_size: int = 512,
        chunk_overlap: int = 128,
        recursive_separators: Optional[List[str]] = None,
        char_separator: Optional[str] = "\n\n",
        keep_separator: bool = True,
        is_separator_regex: bool = False,
        model_name: Optional[str] = "gpt-4",
        **kwargs,
    ) -> Union[RecursiveCharacterTextSplitter, CharacterTextSplitter]:
        """
        Returns an instance of a text splitter based on the provided parameters.

        :param splitter_type: The type of splitter to use. Can be "recursive" or "character". If not found, the character
        splitter will be used. Defaults to "recursive".
        :param use_encoder: Boolean flag to choose whether to use an encoder for the splitter. Defaults to True.
        :param chunk_size: The number of characters in each text chunk. Defaults to 512.
        :param chunk_overlap: The number of characters to overlap between chunks. Defaults to 128.
        :param recursive_separators: List of strings or regex patterns to use as separators for splitting with
          RecursiveCharacterTextSplitter. Only applicable if splitter_type is "recursive".
        :param char_separator: String or regex pattern to use as a separator for splitting with CharacterTextSplitter. Only
        applicable if splitter_type is "character".
        :param keep_separator: Whether to keep the separators in the resulting chunks. Defaults to True.
        :param is_separator_regex: Treat the separators as regex patterns. Defaults to False.
        :param model_name: The name of the model to use for encoding, if use_encoder is True. Defaults to "gpt-4".
        :param kwargs: Additional keyword arguments to pass to the splitter class.
        :return: An instance of either RecursiveCharacterTextSplitter or CharacterTextSplitter.
        :raises ValueError: If use_encoder is True but model_name is not provided.
        :raises Exception: If there's an error while creating the splitter.
        """
        try:
            logger.info(f"Creating a splitter of type: {splitter_type}")
            if splitter_type == "by_character_recursive":
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
            elif splitter_type == "by_title_brute_force":
                encodername = encoding_name_for_model(model_name)
                logger.info(f"Using tiktoken encoder: {encodername}")
                return MarkdownTextSplitter.from_tiktoken_encoder(
                    encoding_name=encodername,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )

            elif splitter_type == "by_character_brute_force":
                if use_encoder:
                    if model_name is None:
                        raise ValueError(
                            "Model name must be provided. if use_encoder is True."
                        )
                    encodername = encoding_name_for_model(model_name)
                    logger.info(f"Using tiktoken encoder: {encodername}")
                    return CharacterTextSplitter.from_tiktoken_encoder(
                        encoding_name=encodername,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        separators=recursive_separators,
                        keep_separator=keep_separator,
                        is_separator_regex=is_separator_regex,
                        **kwargs,
                    )
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
        self,
        documents: List[Document],
        splitter_type: Literal[
            "by_character_recursive", "by_character_brute_force", "by_title_brute_force"
        ] = "by_character_recursive",
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
        Splits documents into smaller chunks.

        :param documents: List of Document objects to split.
        :param splitter_type: Type of splitter ("recursive", "tiktoken", "spacy", "character"). Defaults to "recursive".
        :param use_encoder: If True, uses an encoder for the splitter. Defaults to True.
        :param chunk_size: Number of characters in each chunk. Defaults to 512.
        :param chunk_overlap: Number of characters to overlap between chunks. Defaults to 128.
        :param recursive_separators: List of separators for RecursiveCharacterTextSplitter.
        :param char_separator: Separator for CharacterTextSplitter.
        :param keep_separator: If True, keeps the separators in the chunks. Defaults to True.
        :param is_separator_regex: If True, treats the separators as regex. Defaults to False.
        :param model_name: Name of the model for encoding, if use_encoder is True. Defaults to "gpt-4".
        :param verbose: If True, logs detailed information about the chunks. Defaults to False.
        :param kwargs: Additional arguments for the splitter class.
        :return: List of Document objects representing the chunks.
        :raises Exception: If there's an error while creating the splitter or splitting the text.
        """
        try:
            text_splitter = self.get_splitter(
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
