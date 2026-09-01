# Third Party
from typing import Annotated, TypedDict
import operator
from langchain_core.documents import Document
from langgraph.graph.message import add_messages


class AnalystState(TypedDict):
    #question is the user query
    question: str
    #documents are the context retrieved by retriever 
    documents: Annotated[
        list[Document], 
        operator.add
    ]
    #messages gets appended by user messages and ai messages sequentially 
    messages: Annotated[
        list,
        add_messages,
    ]
    #counts number of times a tool was called to avoid infinite loop of calling tools without answering
    tool_calls_count: int
    #retrieval query is a more specific query when analyst wants more infor from retriever
    retrieval_query: str
