.PHONY: install format lint fix check run clean

# Install dependencies
install:
	pip install -r requirements.txt

create:
	conda create -n docu-agents python=3.12

activate:
	conda activate docu-agents


# Format code using Ruff
format:
	ruff format .


# Lint code
lint:
	ruff check .


# Auto-fix lint issues
fix:
	ruff check . --fix


# Run formatting + lint fixes
check: fix format




# Run individual agents components	
agents:
	python -m src.agents.analyst
	python -m src.agents.answer
	python -m src.agents.retriever

# Run individual graph components	
graph:
	python -m src.graph.nodes
	python -m src.graph.edges
	python -m src.graph.state
	python -m src.graph.workflow


# Run individual ingestion components	
ingestion:
	python -m src.ingestion.chunker
	python -m src.ingestion.cleaner
	python -m src.ingestion.embedder
	python -m src.ingestion.loader
	python -m src.ingestion.pipeline


# Run individual retrieval components	
ingestion:
	python -m src.retrieval.context_selector
	python -m src.retrieval.semantic_search
	python -m src.retrieval.metadata_filter
	python -m src.retrieval.hybrid_search
	python -m src.retrieval.keyword_search
	python -m src.retrieval.vector_store
	python -m src.retrieval.reranker


# Run individual tools components	
memory:
	python -m src.tools.data_analysis
	python -m src.tools.table_extractor
	python -m src.tools.calculator
	python -m src.tools.document_comparator

# Run individual main	
main:
	python -m src.main




###############################################



# Remove Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete