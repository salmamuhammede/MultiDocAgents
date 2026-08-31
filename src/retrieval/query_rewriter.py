from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from loguru import logger

from src.config.prompts.retriever import (
    RETRIEVER_QUERY_REWRITE_PROMPT,
)
from src.config.settings import (
    BASE_URL,
    LLM_API_KEY,
    LLM_MODEL_NAME,
    REWRITER_TIMEOUT,
    TEMPERATURE,
)


class QueryRewriter:
    """
    Rewrite user queries into retrieval-friendly queries.

    Responsibilities:
    - Resolve vague references.
    - Expand abbreviations.
    - Clarify terminology.
    - Preserve important technical terms.
    - Produce a query optimized for document retrieval.

    This class does NOT perform document retrieval.
    """

    def __init__(self) -> None:

        self.llm = ChatOpenAI(
            model=LLM_MODEL_NAME,
            api_key=LLM_API_KEY,
            base_url=BASE_URL,
            temperature=TEMPERATURE,
            timeout=REWRITER_TIMEOUT,
        )

        self.prompt = ChatPromptTemplate.from_template(RETRIEVER_QUERY_REWRITE_PROMPT)

        self.chain = self.prompt | self.llm

        logger.info("Query Rewriter initialized.")

    def rewrite(
        self,
        query: str,
        conversation_history: str = "",
    ) -> str:
        """
        Rewrite a user query for better document retrieval.

        Args:
            query: Original user question.
            conversation_history: Previous conversation
                used to resolve references.

        Returns:
            Rewritten retrieval query.
        """

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        logger.info(f"Rewriting query: {query}")

        response = self.chain.invoke(
            {
                "query": query,
                "conversation_history": conversation_history,
            }
        )

        rewritten_query = response.content.strip()

        if not rewritten_query:
            logger.warning(
                "Query rewriter returned an empty query. Using original query."
            )
            return query

        logger.success(f"Rewritten query: {rewritten_query}")

        return rewritten_query


def main() -> None:

    rewriter = QueryRewriter()

    query = "What are its disadvantages?"

    history = """
User: What is Retrieval-Augmented Generation (RAG)?
Assistant: RAG is a technique that retrieves relevant
documents and provides them to an LLM.
"""

    rewritten_query = rewriter.rewrite(
        query=query,
        conversation_history=history,
    )

    print("Original:")
    print(query)

    print("\nRewritten:")
    print(rewritten_query)


if __name__ == "__main__":
    main()
