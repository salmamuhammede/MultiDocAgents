# Standard library

# Third-party
from langchain_core.documents import Document
from loguru import logger

# Local
from src.retrieval.vector_store import VectorDB


class SemanticSearch:
    """
    Perform semantic similarity search over the vector database.
    """

    def __init__(self, vector_db: VectorDB) -> None:
        self.vector_db = vector_db

    def search(
        self,
        query: str,
        k: int = 10,
    ) -> list[Document]:
        """
        Retrieve the most semantically relevant chunks.
        """

        if not query.strip():
            logger.warning("Empty search query.")
            return []

        logger.info(f"Semantic search: query='{query}', k={k}")

        results = self.vector_db.similarity_search(
            query=query,
            k=k,
        )

        logger.success(f"Semantic search returned {len(results)} results.")

        return results
