from src.ingestion.embedder import EmbeddingModel
from src.retrieval.hybrid_search import HybridSearch
from src.retrieval.keyword_search import KeywordSearch
from src.retrieval.semantic_search import SemanticSearch
from src.retrieval.vector_store import VectorDB


def main():

    query = "Why Use Streamlit?"

    # Setup
    embeddings = EmbeddingModel().get_embeddings()
    vector_db = VectorDB(embeddings)

    # Semantic
    semantic_search = SemanticSearch(vector_db)

    # Keyword
    documents = vector_db.get_all_documents()
    keyword_search = KeywordSearch(documents)

    # Hybrid
    hybrid_search = HybridSearch(
        semantic_search=semantic_search,
        keyword_search=keyword_search,
    )

    # -------------------------
    # Semantic Search
    # -------------------------

    print("\n" + "=" * 60)
    print("SEMANTIC SEARCH")
    print("=" * 60)

    semantic_results = semantic_search.search(
        query=query,
        k=10,
    )

    for i, document in enumerate(semantic_results, 1):
        print(f"\n{i}. Page: {document.metadata.get('page')}")
        print(document.page_content[:300])

    # -------------------------
    # Keyword Search
    # -------------------------

    print("\n" + "=" * 60)
    print("KEYWORD SEARCH")
    print("=" * 60)

    keyword_results = keyword_search.search(
        query=query,
        k=10,
    )

    for i, (document, score) in enumerate(keyword_results, 1):
        print(f"\n{i}. Score: {score}")
        print(f"Page: {document.metadata.get('page')}")
        print(document.page_content[:300])

    # -------------------------
    # Hybrid Search
    # -------------------------

    print("\n" + "=" * 60)
    print("HYBRID SEARCH")
    print("=" * 60)

    hybrid_results = hybrid_search.search(
        query=query,
        k=10,
    )

    for i, (document, score) in enumerate(hybrid_results, 1):
        print(f"\n{i}. Score: {score:.4f}")
        print(f"Page: {document.metadata.get('page')}")
        print(document.page_content[:300])


if __name__ == "__main__":
    main()
