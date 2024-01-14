import fnmatch
import re

from langchain.document_loaders import (
    CSVLoader,
    Docx2txtLoader,
    JSONLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
)

FILE_TYPE_MAPPINGS_LANGCHAIN = {
    re.compile(fnmatch.translate(pattern)): loader_class
    for pattern, loader_class in {
        "*.txt": TextLoader,
        "*.pdf": PyPDFLoader,
        "*.csv": CSVLoader,
        "*.docx": Docx2txtLoader,
        "*.xlss": UnstructuredExcelLoader,
        "*.xlsx": UnstructuredExcelLoader,
        "*.html": UnstructuredHTMLLoader,
        "*.pptx": UnstructuredPowerPointLoader,
        "*.ppt": UnstructuredPowerPointLoader,
        "*.md": UnstructuredMarkdownLoader,
        "*.json": JSONLoader,
    }.items()
}
