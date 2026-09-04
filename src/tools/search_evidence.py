import json

from langchain_core.tools import tool
from loguru import logger


@tool
def search_more_evidence(query: str) -> str:
    """
    Request additional evidence from the document retriever when
    the currently retrieved evidence is insufficient.

    The query must specifically describe the missing information.
    """

    logger.info(f"Search more evidence requested: {query}")

    return json.dumps(
        {
            "type": "additional_retrieval",
            "query": query,
        }
    )
