"""Admin repository interface for administrative operations.

These operations are separated from IRepository because they are:
1. Not part of domain retrieval logic
2. Potentially dangerous (clean_all)
3. Not required by all consumers
"""

from abc import ABC, abstractmethod


class IAdminRepository(ABC):
    """Interface for administrative database operations.

    Separate from IRepository to avoid forcing all consumers
    to implement admin operations they don't need.
    """

    @abstractmethod
    async def clean_all(self) -> None:
        """Clear all documents and chunks.

        Use with caution - this operation is irreversible.
        Typically used for testing or resetting the database.
        """
        pass

    @abstractmethod
    async def get_stats(self) -> dict:
        """Get database statistics.

        Returns:
            Dict with keys like 'document_count', 'chunk_count', 'storage_bytes'.
        """
        pass
