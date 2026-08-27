# Standard library
from typing import Any

# Third-party
from langchain_core.documents import Document
from loguru import logger

# Local


class MetadataFilter:
    """
    Filter retrieved documents based on their metadata.

    Examples of metadata:
        - source
        - page
        - file_type
        - chapter
        - section
        - author
    """

    def filter(
        self,
        documents: list[Document],
        filters: dict[str, Any],
    ) -> list[Document]:
        """
        Keep only documents whose metadata matches
        the provided filters.

        Args:
            documents: Retrieved document chunks.
            filters: Metadata conditions to apply.

        Returns:
            Filtered list of documents.
        """

        if not documents:
            logger.warning("No documents provided for filtering.")
            return []

        if not filters:
            logger.info("No metadata filters provided.")
            return documents

        logger.info(f"Applying metadata filters: {filters}")

        filtered_documents = []

        for document in documents:
            if self._matches_filters(
                document,
                filters,
            ):
                filtered_documents.append(document)

        logger.info(
            f"Metadata filtering: "
            f"{len(documents)} → {len(filtered_documents)} documents"
        )

        return filtered_documents

    @staticmethod
    def _matches_filters(
        document: Document,
        filters: dict[str, Any],
    ) -> bool:
        """
        Check whether a document satisfies all metadata filters.
        """

        metadata = document.metadata

        for key, expected_value in filters.items():
            actual_value = metadata.get(key)

            if actual_value != expected_value:
                return False

        return True
