import logging
import os
from typing import List

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain.text_splitter import MarkdownTextSplitter
from pydantic import BaseModel

from src.enrichers.ocr_document_intelligence import AzureDocumentIntelligenceManager

load_dotenv()

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)


class RecordData(BaseModel):
    url: str


class Record(BaseModel):
    recordId: str
    data: RecordData
    chunk_size: int
    chunk_overlap: int


class RequestBody(BaseModel):
    values: List[Record]


app = FastAPI()

DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
DOCUMENT_INTELLIGENCE_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
BLOB_CONNECTION_STRING = os.getenv("STORAGE_CONNNECTION_STRING")

az_intel = AzureDocumentIntelligenceManager(
    azure_endpoint=DOCUMENT_INTELLIGENCE_ENDPOINT, azure_key=DOCUMENT_INTELLIGENCE_KEY
)


@app.post("/createChunks")
async def vectorize(request_body: RequestBody):
    # json response
    json_response = {"values": []}

    # skill can receive multiple records at a time
    for record in request_body.values:
        url = record.data.url
        logger.info(f"input url: {url}")

        # getting vector for image in url
        logger.info("getting vector...")
        result_ocr = az_intel.analyze_document(
            document_input=url,
            model_type="prebuilt-layout",
            output_format="markdown",
            features=["OCR_HIGH_RESOLUTION"],
        )

        logger.info(result_ocr.content)

        if result_ocr:
            # add json to json_response values
            splitter = MarkdownTextSplitter.from_tiktoken_encoder(
                chunk_size=record.chunk_size, chunk_overlap=record.chunk_overlap
            )

            chunked_content_list = splitter.split_text(result_ocr.content)
            logger.info(chunked_content_list)

            for idx, chunked_content in enumerate(chunked_content_list):
                # Process the chunked content here, for example, get vector and description
                json_response["values"].append(
                    {
                        "recordId": f"{record.recordId}",
                        "data": {"chunk": chunked_content, "chunkId": idx},
                        "errors": [],
                    }
                )
        else:
            logger.info("No chunks created")

            # add json with error to json_response values
            json_response["values"].append(
                {
                    "recordId": record.recordId,
                    "data": {},
                    "errors": [{"message": "No chunks created from the document"}],
                }
            )

    return json_response


# Run the server
if __name__ == "__main__":
    import uvicorn  # noqa: F811

    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=60)
