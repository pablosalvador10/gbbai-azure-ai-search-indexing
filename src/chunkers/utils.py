from typing import List

import tiktoken
from langchain.docstore.document import Document

from src.aoai.settings import encoding_name_for_model


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
