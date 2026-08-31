# Third Party
from typing import Annotated, TypedDict

from langchain_core.documents import Document
from langgraph.graph.message import add_messages


class AnalystState(TypedDict):

    question: str

    documents: list[Document]

    messages: Annotated[
        list,
        add_messages,
    ]

    tool_calls_count: int
