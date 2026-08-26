| Person 1 — RAG & Retriever          | Person 2 — Analyst & Answer        |
| ----------------------------------- | ---------------------------------- |
| `src/ingestion/__init__.py`         | `src/agents/__init__.py`           |
| `src/ingestion/loader.py`           | `src/agents/analyst.py`            |
| `src/ingestion/cleaner.py`          | `src/agents/answer.py`             |
| `src/ingestion/chunker.py`          | `src/tools/__init__.py`            |
| `src/ingestion/embedder.py`         | `src/tools/calculator.py`          |
| `src/ingestion/pipeline.py`         | `src/tools/table_extractor.py`     |
| `src/retrieval/__init__.py`         | `src/tools/document_comparator.py` |
| `src/retrieval/vector_store.py`     | `src/tools/data_analysis.py`       |
| `src/retrieval/semantic_search.py`  | `src/config/prompts/analyst.py`    |
| `src/retrieval/keyword_search.py`   | `src/config/prompts/answer.py`     |
| `src/retrieval/hybrid_search.py`    |                                    |
| `src/retrieval/metadata_filter.py`  |                                    |
| `src/retrieval/reranker.py`         |                                    |
| `src/retrieval/context_selector.py` |                                    |
| `src/agents/retriever.py`           |                                    |
| `src/config/prompts/retriever.py`   |                                    |


| Shared                           |
| -------------------------------- |
| `src/main.py`                    |
| `src/config/settings.py`         |
| `src/graph/state.py`             |
| `src/graph/nodes.py`             |
| `src/graph/edges.py`             |
| `src/graph/workflow.py`          |
| `README.md`                      |
| `requirements.txt`               |
| `.gitignore`                     |
