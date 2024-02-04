"""
This module defines the abstract base class for splitting documents into chunks using different strategies.
"""
from abc import ABC, abstractmethod
from typing import List

from langchain.docstore.document import Document

from src.aoai.tokenizer import AzureOpenAITokenizer


class DocumentSplitter(ABC):
    """
    Abstract base class for splitting documents into chunks.

    This class defines the interface for splitting documents into chunks. It includes an abstract
    method `split_documents_in_chunks_from_documents` that takes a list of Document objects and returns a
    list of Document objects representing the chunks. Subclasses should implement this method to provide specific
    document splitting functionality.
    """

    def __init__(self):
        self.tokenizer = AzureOpenAITokenizer()

    @abstractmethod
    def split_documents_in_chunks_from_documents(
        self, documents: List[Document]
    ) -> List[Document]:
        """
        Abstract method to split a list of Document objects into chunks.

        :param documents: A list of Document objects to split.
        :return: A list of Document objects representing the chunks.
        """
        pass
