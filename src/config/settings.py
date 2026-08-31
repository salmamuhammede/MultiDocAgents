import os

from dotenv import load_dotenv

load_dotenv()


# ==============================
# Document Ingestion
# ==============================

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


# ==============================
# Embeddings
# ==============================

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DEVICE = "cpu"


# ==============================
# Vector Database
# ==============================

CHROMA_DB_PATH = "data/chroma_db"
COLLECTION_NAME = "documents"


# ==============================
# Retrieval
# ==============================

SEMANTIC_TOP_K = 20
KEYWORD_TOP_K = 20
HYBRID_TOP_K = 20
RERANK_TOP_K = 10
CONTEXT_TOP_K = 5


# ==============================
# Reranker
# ==============================

RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"
RERANKER_DEVICE = "cpu"


# ==============================
# LLM
# ==============================

BASE_URL = "https://openrouter.ai/api/v1"

LLM_MODEL_NAME = "openrouter/free"

LLM_API_KEY = os.getenv("OPENROUTER_API_KEY")
ANALYST_API_KEY = os.getenv("ANALYST_API_KEY")
COMPARATOR_API_KEY = os.getenv("COMPARATOR_API_KEY")

TEMPERATURE = 0.2


# ==============================
# Documents
# ==============================

UPLOAD_DIR = "data/uploads"
PDF_DOC_TEST = "data/uploads/gdp.pdf"

# ==============================
#Timeouts and maxlimits
# ==============================
MAX_TOOL_CALLS = 5
REWRITER_TIMEOUT = 60
ANALYST_TIMEOUT = 60
