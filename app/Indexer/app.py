import logging
from enum import Enum
from typing import List, Union

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

# Import the AzureAIndexer class from the ai_search_indexing module
from src.indexers.ai_search_indexing import AzureAIndexer

# Load environment variables
load_dotenv()

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)


class SplitterType(str, Enum):
    by_title = "by_title"
    by_character_recursive = "by_character_recursive"
    by_character_brute_force = "by_character_brute_force"


class OCRFormat(str, Enum):
    markdown = "markdown"
    text = "text"


class IndexerConfig(BaseModel):
    index_name: str = Field(..., description="The name of the index to use.")
    embedding_azure_deployment_name: str = Field(
        ..., description="The model name for embedding or processing."
    )


class SplitterParams(BaseModel):
    splitter_type: SplitterType
    ocr: bool
    ocr_output_format: OCRFormat
    pages: str
    use_encoder: bool
    chunk_size: int
    chunk_overlap: int
    verbose: bool
    keep_separator: bool
    is_separator_regex: bool


class DocumentChunkRequest(BaseModel):
    file_paths: Union[str, List[str]]
    splitter_params: SplitterParams
    indexer_config: IndexerConfig


# Initialize the FastAPI application
app = FastAPI()


@app.post("/indexing_documents")
async def indexing_documents(request: DocumentChunkRequest):
    # Extract the file_paths, splitter_params, and indexer_config from the request
    file_paths = request.file_paths
    splitter_params = (
        request.splitter_params.dict()
    )  # Convert to dictionary for unpacking
    indexer_config = (
        request.indexer_config.dict()
    )  # Convert to dictionary for unpacking

    # Initialize the AzureAIndexer client with indexer_config
    azure_search_indexer_client = AzureAIndexer(**indexer_config)

    # Initialize lists to keep track of failed and successful files
    failed_files: List[str] = []
    successful_files: List[str] = []

    # Initialize a variable to keep track of the total number of chunks
    total_chunks = 0

    # Loop over the file paths and process each one individually
    for file_path in file_paths:
        # Process files and split into chunks
        document_chunks_to_index = (
            azure_search_indexer_client.load_files_and_split_into_chunks(
                file_paths=[file_path],
                **splitter_params,
            )
        )

        # Update the total number of chunks
        total_chunks += len(document_chunks_to_index)

        # Index the document chunks using the Azure Search Indexer client
        success = azure_search_indexer_client.index_text_embeddings(
            document_chunks_to_index
        )

        # If any operation fails, add the file to the failed_files list
        # Otherwise, add it to the successful_files list
        if not success:
            logger.warning(f"Failed to process file: {file_path}")
            failed_files.append(file_path)
        else:
            successful_files.append(file_path)

    # Retry logic for failed files
    for file_path in failed_files:
        logger.info(f"Retrying file: {file_path}")
        # Process files and split into chunks
        document_chunks_to_index = (
            azure_search_indexer_client.load_files_and_split_into_chunks(
                file_paths=[file_path],
                **splitter_params,
            )
        )

        # Index the document chunks using the Azure Search Indexer client
        success = azure_search_indexer_client.index_text_embeddings(
            document_chunks_to_index
        )

        # If the operation fails again, log the failure
        # Otherwise, move the file from the failed_files list to the successful_files list
        if not success:
            logger.error(f"Failed to process file after retry: {file_path}")
        else:
            failed_files.remove(file_path)
            successful_files.append(file_path)

    return {
        "message": "Documents processed",
        "successful_files": successful_files,
        "failed_files": failed_files,
        "total_chunks": total_chunks,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
