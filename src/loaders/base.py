from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from langchain.docstore.document import Document

from src.chunkers.settings import FILE_TYPE_MAPPINGS_LANGCHAIN


class DocumentLoaders(ABC):
    """
    Abstract base class for document loaders.

    This class defines the interface for document loaders. Subclasses should implement these methods to provide
    specific document loading functionality.
    """

    def __init__(self):
        self.langchain_file_mapping = FILE_TYPE_MAPPINGS_LANGCHAIN

    @abstractmethod
    def load_document(
        self,
        file_path: Optional[str] = None,
        file_url: Optional[str] = None,
        file_extension: Optional[str] = None,
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Dict[str, Any],
    ) -> Document:
        """
        Abstract method to load a single document.

        Subclasses should implement this method to provide specific document loading functionality.
        """
        pass

    @abstractmethod
    def load_documents(
        self, file_paths: Optional[Union[str, List[str]]] = None, **kwargs
    ) -> List[Document]:
        """
        Abstract method to load multiple documents.

        Subclasses should implement this method to provide specific document loading functionality.
        """
        pass
