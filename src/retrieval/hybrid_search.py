# Standard library
from collections import defaultdict

# Third-party
from langchain_core.documents import Document
from loguru import logger

# Local
from src.retrieval.keyword_search import KeywordSearch
from src.retrieval.semantic_search import SemanticSearch


class HybridSearch:
    """
    Combine semantic search and keyword search.

    Uses Weighted Reciprocal Rank Fusion (RRF) to combine
    the rankings from both retrieval methods.

    Semantic search has a higher weight by default because
    it is generally better at understanding the meaning of
    natural-language queries.
    """

    def __init__(
        self,
        semantic_search: SemanticSearch,
        keyword_search: KeywordSearch,
    ) -> None:
        self.semantic_search = semantic_search
        self.keyword_search = keyword_search

    def search(
        self,
        query: str,
        k: int = 10,
        semantic_k: int = 20,
        keyword_k: int = 10,
        rrf_k: int = 60,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> list[tuple[Document, float]]:
        """
        Perform hybrid retrieval using weighted RRF.

        Args:
            query:
                User search query.

            k:
                Number of final results returned by hybrid search.

            semantic_k:
                Number of candidates retrieved by semantic search.

            keyword_k:
                Number of candidates retrieved by keyword search.

            rrf_k:
                RRF constant used to reduce the impact of
                lower-ranked documents.

            semantic_weight:
                Weight assigned to semantic search.

            keyword_weight:
                Weight assigned to keyword search.

        Returns:
            List of (Document, hybrid_score) tuples.
        """

        if not query.strip():
            logger.warning("Empty hybrid search query.")
            return []

        if k <= 0:
            raise ValueError("k must be greater than 0.")

        if semantic_k <= 0:
            raise ValueError("semantic_k must be greater than 0.")

        if keyword_k <= 0:
            raise ValueError("keyword_k must be greater than 0.")

        if rrf_k < 0:
            raise ValueError("rrf_k must be greater than or equal to 0.")

        if semantic_weight < 0:
            raise ValueError("semantic_weight cannot be negative.")

        if keyword_weight < 0:
            raise ValueError("keyword_weight cannot be negative.")

        if semantic_weight == 0 and keyword_weight == 0:
            raise ValueError("At least one search weight must be greater than 0.")

        logger.info(f"Starting hybrid search: query='{query}'")

        logger.debug(
            f"Search configuration: "
            f"semantic_k={semantic_k}, "
            f"keyword_k={keyword_k}, "
            f"semantic_weight={semantic_weight}, "
            f"keyword_weight={keyword_weight}, "
            f"rrf_k={rrf_k}"
        )

        # --------------------------------------------------
        # 1. Semantic Search
        # --------------------------------------------------

        semantic_results = self.semantic_search.search(
            query=query,
            k=semantic_k,
        )

        logger.debug(f"Semantic search returned {len(semantic_results)} candidates.")

        # --------------------------------------------------
        # 2. Keyword Search
        # --------------------------------------------------

        keyword_results = self.keyword_search.search(
            query=query,
            k=keyword_k,
        )

        logger.debug(f"Keyword search returned {len(keyword_results)} candidates.")

        # --------------------------------------------------
        # 3. Weighted Reciprocal Rank Fusion
        # --------------------------------------------------

        scores = defaultdict(float)
        documents: dict[str, Document] = {}

        # --------------------------------------------------
        # Semantic ranking
        # --------------------------------------------------

        for rank, document in enumerate(
            semantic_results,
            start=1,
        ):
            document_id = self._get_document_id(document)

            semantic_score = semantic_weight / (rrf_k + rank)

            scores[document_id] += semantic_score
            documents[document_id] = document

        # --------------------------------------------------
        # Keyword ranking
        # --------------------------------------------------

        for rank, (document, _) in enumerate(
            keyword_results,
            start=1,
        ):
            document_id = self._get_document_id(document)

            keyword_score = keyword_weight / (rrf_k + rank)

            scores[document_id] += keyword_score
            documents[document_id] = document

        # --------------------------------------------------
        # 4. Sort by fused score
        # --------------------------------------------------

        ranked_results = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        # --------------------------------------------------
        # 5. Return top-k
        # --------------------------------------------------

        results = [
            (
                documents[document_id],
                score,
            )
            for document_id, score in ranked_results[:k]
        ]

        logger.success(f"Hybrid search returned {len(results)} results.")

        return results

    @staticmethod
    def _get_document_id(
        document: Document,
    ) -> str:
        """
        Generate a stable identifier for a document chunk.

        Uses the source, page, and chunk content when
        available.
        """

        metadata = document.metadata

        source = metadata.get(
            "source",
            "unknown",
        )

        page = metadata.get(
            "page",
            "",
        )

        content = document.page_content

        return f"{source}_{page}_{hash(content)}"
