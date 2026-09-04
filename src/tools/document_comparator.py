# Third Party
from typing import Annotated

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import InjectedState
from loguru import logger
from pydantic import BaseModel, Field

# local
from src.config.prompts.analyst import COMPARATOR_PROMPT
from src.config.settings import (
    BASE_URL,
    COMPARATOR_API_KEY,
    LLM_MODEL_NAME,
    TEMPERATURE,
)

# ============================================================
# Structured Output
# ============================================================


class Evidence(BaseModel):
    document_id: str = Field(description="ID of the source document")
    document_name: str = Field(description="Name of the source document")
    chunk_id: str = Field(description="ID of the retrieved chunk")
    claim: str = Field(description="Claim extracted from the chunk")
    source_text: str = Field(description="Relevant source text")


class DocumentAnalysis(BaseModel):
    document_id: str
    document_name: str

    methodology: str = ""
    dataset: str = ""
    metrics: list[str] = Field(default_factory=list)
    results: list[str] = Field(default_factory=list)

    advantages: list[str] = Field(default_factory=list)
    disadvantages: list[str] = Field(default_factory=list)

    conclusions: str = ""
    limitations: list[str] = Field(default_factory=list)

    evidence: list[Evidence] = Field(default_factory=list)


class ComparisonResult(BaseModel):
    comparison_topic: str

    comparability: str = Field(
        description=(
            "Whether the documents can be fairly compared. "
            "Explain important differences in datasets, metrics, "
            "experimental conditions, etc."
        )
    )

    documents: list[DocumentAnalysis]

    similarities: list[str] = Field(default_factory=list)

    differences: list[str] = Field(default_factory=list)

    important_observations: list[str] = Field(default_factory=list)


# ============================================================
# Document Comparison Tool
# ============================================================


class DocumentComparisonTool:
    """
    Compares information retrieved from multiple documents.

    The tool does NOT answer the user's question directly.
    It organizes evidence so that the Analyst Agent can reason
    over the comparison.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=COMPARATOR_API_KEY,
            base_url=BASE_URL,
            model=LLM_MODEL_NAME,
            temperature=TEMPERATURE,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    COMPARATOR_PROMPT,
                ),
                (
                    "human",
                    """
                    User Query:
                    {query}

                    Retrieved Documents:

                    {documents}
                    """,
                ),
            ]
        )

        # Force the LLM to return our Pydantic schema
        self.chain = self.prompt | self.llm.with_structured_output(ComparisonResult)

        self.compare_documents = tool(self._compare_documents)

    # --------------------------------------------------------
    # Format retrieved chunks
    # --------------------------------------------------------
    @staticmethod
    def convert_langchain_documents(docs):
        documents = []

        for i, doc in enumerate(docs):
            metadata = doc.metadata

            documents.append(
                {
                    "document_id": metadata.get(
                        "document_id", metadata.get("source", f"document_{i}")
                    ),
                    "document_name": metadata.get(
                        "document_name", metadata.get("source", f"document_{i}")
                    ),
                    "chunk_id": metadata.get("chunk_id", f"chunk_{i}"),
                    "text": doc.page_content,
                    "page": metadata.get("page"),
                    "section": metadata.get("section"),
                }
            )

        return documents

    # --------------------------------------------------------
    # Compare
    # --------------------------------------------------------

    def _compare_documents(
        self,
        question: str,
        documents: Annotated[list[Document], InjectedState("documents")],
    ) -> str:
        """
        Compare information across multiple retrieved documents.

        Use this tool when the user asks to compare documents,
        methodologies, models, results, advantages, disadvantages,
        similarities, or differences.

        The retrieved documents are automatically provided by
        the Analyst graph state.
        """

        logger.info("Document Comparison tool called")

        formatted_documents = self.convert_langchain_documents(documents)

        documents_text = "\n\n".join(
            f"""
    Document: {doc["document_name"]}
    Document ID: {doc["document_id"]}
    Chunk ID: {doc["chunk_id"]}
    Page: {doc["page"]}
    Section: {doc["section"]}

    Content:
    {doc["text"]}
    """
            for doc in formatted_documents
        )

        result = self.chain.invoke(
            {
                "query": question,
                "documents": documents_text,
            }
        )

        return result.model_dump_json(indent=2)
