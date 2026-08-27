# Standard library

# Third-party
from langchain_core.documents import Document
from loguru import logger
from rank_bm25 import BM25Okapi

# Local


class KeywordSearch:
    """
    Perform keyword-based retrieval using BM25.

    BM25 focuses on lexical matching between the query
    and document chunks.
    """

    def __init__(
        self,
        documents: list[Document],
    ) -> None:
        self.documents = documents

        if not documents:
            raise ValueError("KeywordSearch requires at least one document.")

        # Tokenize documents
        tokenized_documents = [
            self._tokenize(document.page_content) for document in documents
        ]

        # Build BM25 index
        self.bm25 = BM25Okapi(tokenized_documents)

        logger.info(f"BM25 index created with {len(documents)} documents.")

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """
        Convert text into tokens for BM25.
        """

        return text.lower().split()

    def search(
        self,
        query: str,
        k: int = 10,
    ) -> list[tuple[Document, float]]:
        """
        Search documents using BM25.

        Returns:
            List of (Document, score) tuples.
        """

        if not query.strip():
            logger.warning("Empty keyword search query.")
            return []

        if k <= 0:
            raise ValueError("k must be greater than 0.")

        # Tokenize query
        tokenized_query = self._tokenize(query)

        # Calculate BM25 scores
        scores = self.bm25.get_scores(tokenized_query)

        # Get indices of highest scores
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )

        # Keep only top-k
        ranked_indices = ranked_indices[:k]

        results = [
            (
                self.documents[index],
                float(scores[index]),
            )
            for index in ranked_indices
        ]

        logger.info(f"Keyword search returned {len(results)} results.")

        return results
