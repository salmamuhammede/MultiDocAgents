from langchain_core.documents import Document
from loguru import logger

# Ingestion
from src.ingestion.embedder import EmbeddingModel

# Retrieval
from src.retrieval.context_selector import ContextSelector
from src.retrieval.hybrid_search import HybridSearch
from src.retrieval.keyword_search import KeywordSearch
from src.retrieval.metadata_filter import MetadataFilter
from src.retrieval.query_rewriter import QueryRewriter
from src.retrieval.reranker import Reranker
from src.retrieval.semantic_search import SemanticSearch
from src.retrieval.vector_store import VectorDB


class RetrieverAgent:
    """
    Retriever Agent.

    Responsible for:
    1. Rewriting the user's query.
    2. Retrieving candidate documents using hybrid search.
    3. Applying metadata filters.
    4. Reranking the retrieved documents.
    5. Selecting the final evidence.

    The Retriever Agent does NOT answer the user's question.
    It only returns relevant evidence for the Analyst Agent.

    By default, the agent initializes the complete retrieval
    pipeline internally.
    """

    def __init__(
        self,
        query_rewriter: QueryRewriter | None = None,
        hybrid_search: HybridSearch | None = None,
        metadata_filter: MetadataFilter | None = None,
        reranker: Reranker | None = None,
        context_selector: ContextSelector | None = None,
    ) -> None:

        self.query_rewriter = query_rewriter or QueryRewriter()

        if hybrid_search is None:
            logger.info("Building retrieval infrastructure...")

            # 1. Embedding model
            embedding_model = EmbeddingModel()

            embeddings = embedding_model.get_embeddings()

            # 2. Chroma vector database
            vector_db = VectorDB(embeddings)

            # 3. Semantic search
            semantic_search = SemanticSearch(vector_db)

            # 4. Load all chunks for BM25
            all_documents = vector_db.get_all_documents()

            logger.info(f"Loaded {len(all_documents)} documents for keyword search.")

            # 5. Keyword search
            keyword_search = KeywordSearch(all_documents)

            # 6. Hybrid search
            self.hybrid_search = HybridSearch(
                semantic_search=semantic_search,
                keyword_search=keyword_search,
            )

            logger.success("Hybrid retrieval initialized.")

        else:
            self.hybrid_search = hybrid_search

        # 7. Metadata filtering
        self.metadata_filter = metadata_filter or MetadataFilter()

        # 8. Reranker
        self.reranker = reranker or Reranker()

        # 9. Context selection
        self.context_selector = context_selector or ContextSelector()

        logger.success("Retriever Agent initialized.")

    def retrieve(
        self,
        query: str,
        conversation_history: str = "",
        metadata_filters: dict | None = None,
        semantic_k: int = 20,
        keyword_k: int = 20,
        rerank_k: int = 10,
    ) -> list[tuple[Document, float]]:
        """
        Retrieve and rank evidence for a user query.

        Args:
            query:
                Original user question.

            conversation_history:
                Previous conversation used by the query rewriter.

            metadata_filters:
                Optional metadata restrictions.

            semantic_k:
                Number of semantic candidates.

            keyword_k:
                Number of keyword candidates.

            rerank_k:
                Number of documents to keep after reranking.

        Returns:
            Final evidence as:
            [(Document, relevance_score), ...]
        """

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        logger.info(f"Retriever Agent processing: {query}")

        # --------------------------------------------------
        # 1. Rewrite Query
        # --------------------------------------------------

        rewritten_query = self.query_rewriter.rewrite(
            query=query,
            conversation_history=conversation_history,
        )

        logger.info(f"Rewritten query: {rewritten_query}")

        # --------------------------------------------------
        # 2. Hybrid Retrieval
        # --------------------------------------------------

        hybrid_results = self.hybrid_search.search(
            query=rewritten_query,
            k=max(semantic_k, keyword_k),
            semantic_k=semantic_k,
            keyword_k=keyword_k,
        )

        logger.info(f"Hybrid retrieval returned {len(hybrid_results)} candidates.")

        # --------------------------------------------------
        # 3. Extract Documents
        # --------------------------------------------------

        documents = [document for document, _ in hybrid_results]

        if not documents:
            logger.warning("Hybrid search returned no documents.")
            return []

        # --------------------------------------------------
        # 4. Metadata Filtering
        # --------------------------------------------------

        if metadata_filters:
            documents = self.metadata_filter.filter(
                documents=documents,
                filters=metadata_filters,
            )

        logger.info(f"{len(documents)} documents remain after metadata filtering.")

        if not documents:
            logger.warning("No documents remain after filtering.")
            return []

        # --------------------------------------------------
        # 5. Reranking
        # --------------------------------------------------

        reranked_documents = self.reranker.rerank(
            query=rewritten_query,
            documents=documents,
            top_k=rerank_k,
        )

        logger.info(f"Reranking produced {len(reranked_documents)} documents.")

        print("\n" + "=" * 60)
        print("RERANKER RESULTS")
        print("=" * 60)

        for i, (document, score) in enumerate(
            reranked_documents,
            start=1,
        ):
            print(f"\n--- Result {i} ---")
            print(f"Score: {score:.4f}")
            print(f"Page: {document.metadata.get('page', 'N/A')}")
            print(f"Content:\n{document.page_content[:300]}")

        # --------------------------------------------------
        # 6. Context Selection
        # --------------------------------------------------

        final_context = self.context_selector.select(reranked_documents)

        logger.success(
            f"Retriever Agent produced {len(final_context)} final evidence chunks."
        )

        return final_context


def main() -> None:

    logger.info("Testing Retriever Agent")

    # RetrieverAgent builds the retrieval
    # infrastructure automatically.
    retriever = RetrieverAgent()

    query = "What is Streamlit?"

    results = retriever.retrieve(
        query=query,
    )

    print("\n" + "=" * 60)
    print("RETRIEVAL RESULTS")
    print("=" * 60)

    print(f"\nQuery: {query}")
    print(f"Number of results: {len(results)}")

    for i, (document, score) in enumerate(
        results,
        start=1,
    ):
        print(f"\n--- Result {i} ---")

        print(f"Score: {score:.4f}")

        print(f"Source: {document.metadata.get('source')}")

        print(f"Page: {document.metadata.get('page', 'N/A')}")

        print(f"Content:\n{document.page_content[:500]}")


if __name__ == "__main__":
    main()
