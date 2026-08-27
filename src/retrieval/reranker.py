# Standard library

# Third-party
from langchain_core.documents import Document
from loguru import logger
from sentence_transformers import CrossEncoder

# Local
from src.config.settings import RERANKER_DEVICE, RERANKER_MODEL_NAME


class Reranker:
    """
    Rerank retrieved documents using a cross-encoder model.

    The model evaluates the relevance between the query
    and each retrieved document chunk.
    """

    def __init__(
        self,
        model_name: str = RERANKER_MODEL_NAME,
    ) -> None:

        logger.info(f"Loading reranker model: {model_name}")

        self.model = CrossEncoder(
            model_name,
            device=RERANKER_DEVICE,
        )

        logger.success("Reranker model loaded successfully.")

    def rerank(
        self,
        query: str,
        documents: list[Document],
        top_k: int = 5,
    ) -> list[tuple[Document, float]]:
        """
        Rerank documents according to their relevance to the query.

        Args:
            query: User query.
            documents: Candidate documents from retrieval.
            top_k: Number of documents to return.

        Returns:
            List of (Document, relevance_score) tuples.
        """

        if not query.strip():
            logger.warning("Empty reranking query.")
            return []

        if not documents:
            logger.warning("No documents provided for reranking.")
            return []

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        logger.info(f"Reranking {len(documents)} documents...")

        # Create query-document pairs
        pairs = [
            (
                query,
                document.page_content,
            )
            for document in documents
        ]

        # Calculate relevance scores
        scores = self.model.predict(pairs)

        # Combine documents with scores
        scored_documents = [
            (
                document,
                float(score),
            )
            for document, score in zip(
                documents,
                scores,
            )
        ]

        # Sort by relevance score
        scored_documents.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        # Select top-k
        results = scored_documents[:top_k]

        logger.success(f"Reranking completed. Selected {len(results)} documents.")

        return results
