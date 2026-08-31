# Third Party
from typing import Annotated, List, TypedDict

from langchain_core.documents import Document
from langgraph.graph.message import add_messages


class AnalystState(TypedDict):

    question: str

    documents: List[Document]

    messages: Annotated[
        list,
        add_messages,
    ]
