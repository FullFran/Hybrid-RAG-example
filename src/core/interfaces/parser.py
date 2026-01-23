from abc import ABC, abstractmethod
from typing import Any, Optional


class IParser(ABC):
    """Interface for document parsing."""

    @abstractmethod
    async def parse(self, file_path: str) -> tuple[str, Optional[Any]]:
        """
        Parse a document and return its content as markdown and an optional raw document object.

        Args:
            file_path: Path to the document file.

        Returns:
            Tuple of (markdown_content, raw_document).
        """
        pass
