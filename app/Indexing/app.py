"""
This is a FastAPI application that indexes documents from an Azure Blob Storage, splitting them into chunks and retrying failed indexing operations.
"""
import logging
import time
from enum import Enum
from typing import List, Union

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.indexers.ai_search_indexing import AzureAIndexer

load_dotenv()

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)


class SplitterType(str, Enum):
    by_title = "by_title"
    by_character_recursive = "by_character_recursive"
    by_character_brute_force = "by_character_brute_force"
    by_title_brute_force = "by_title_brute_force"


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


class BlobSourceRequest(BaseModel):
    container: str
    updated_since: int
    time_unit: str


class DocumentChunkRequest(BaseModel):
    file_paths: Union[str, List[str]]
    splitter_params: SplitterParams
    indexer_config: IndexerConfig
    # blob_source: BlobSourceRequest


app = FastAPI()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/indexing_documents")
async def indexing_documents(request: DocumentChunkRequest):
    file_paths = request.file_paths
    if file_paths:
        file_paths = file_paths
    # else:
    #     logger.info("file_paths is empty, fetching updated files from Azure Blob Storage.")
    #     data_source_config = request.blob_source
    #     logger.info(f"Container name: {data_source_config.container}")
    #     az_blob = AzureBlobDataExtractor(container_name=data_source_config.container)
    #     file_paths = az_blob.list_updated_files(updated_since=data_source_config.updated_since, time_unit=data_source_config.time_unit)
    #     logger.info(f"Updated file paths: {file_paths}")
    splitter_params = request.splitter_params.dict()
    indexer_config = request.indexer_config.dict()

    azure_search_indexer_client = AzureAIndexer(**indexer_config)

    failed_files: List[str] = []
    successful_files: List[str] = []
    total_chunks = 0
    start_time = time.time()

    for file_path in file_paths:
        try:
            document_chunks_to_index = (
                azure_search_indexer_client.load_files_and_split_into_chunks(
                    file_paths=[file_path],
                    **splitter_params,
                )
            )

            total_chunks += len(document_chunks_to_index)

            success = azure_search_indexer_client.index_text_embeddings(
                document_chunks_to_index
            )

            if not success:
                logger.warning(f"Failed to process file: {file_path}")
                failed_files.append(file_path)
            else:
                successful_files.append(file_path)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            failed_files.append(file_path)

    for file_path in failed_files:
        logger.info(f"Retrying file: {file_path}")
        try:
            document_chunks_to_index = (
                azure_search_indexer_client.load_files_and_split_into_chunks(
                    file_paths=[file_path],
                    **splitter_params,
                )
            )

            success = azure_search_indexer_client.index_text_embeddings(
                document_chunks_to_index
            )

            if not success:
                logger.error(f"Failed to process file after retry: {file_path}")
            else:
                failed_files.remove(file_path)
                successful_files.append(file_path)
        except Exception as e:
            logger.error(f"Error processing file {file_path} on retry: {str(e)}")

    end_time = time.time()
    indexing_time = end_time - start_time

    return {
        "success": len(failed_files) == 0,
        "successful_indexed_files": successful_files,
        "failed_indexed_files": failed_files,
        "total_chunks_indexed": total_chunks,
        "index": request.indexer_config.index_name,
        "indexing_time": indexing_time,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
