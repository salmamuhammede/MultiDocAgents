# Third party
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from loguru import logger

# Local
from src.agents.analyst import AnalystAgent
from src.config.settings import (
    MAX_TOOL_CALLS,
)
from src.graph.nodes import (
    analyze_node,
    final_answer_node,
    more_evidence,
    retrieve,
)
from src.graph.state import AnalystState

# ============================================================
# Create tools
# ============================================================

# initialize analyzer once
analyst = AnalystAgent.load_llm_with_tools()
final_analyst = AnalystAgent.load_llm()

# instantiate memory
memory = MemorySaver()

tools = AnalystAgent.get_tools()

tool_node = ToolNode(tools)

analyze = analyze_node(analyst)
final_answer = final_answer_node(final_analyst)

# ============================================================
# Decide whether Analyst wants to use a tool
# ============================================================


# def should_continue(state):

#     if state.get("tool_calls_count", 0) >= MAX_TOOL_CALLS:
#         return END

#     last_message = state["messages"][-1]

#     tool_calls = getattr(last_message, "tool_calls", [])

#     if not tool_calls:
#         return END

#     for call in tool_calls:
#         if call["name"] == "search_more_evidence":
#             return "more_evidence"

#     return "tools"


def should_continue(state: AnalystState):
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", [])

    # Analyst already produced a final answer
    if not tool_calls:
        return END

    # More evidence → retrieval
    for call in tool_calls:
        if call["name"] == "search_more_evidence":
            return "more_evidence"

    # Normal tools
    tool_calls_count = state.get("tool_calls_count", 0)

    if tool_calls_count >= MAX_TOOL_CALLS:
        logger.warning(f"Maximum tool calls reached: {tool_calls_count}")

        # Do NOT end with a tool-call message
        # Force the final answer
        return "final_answer"

    return "tools"


# ============================================================
# Build graph
# ============================================================

builder = StateGraph(AnalystState)

# Nodes
builder.add_node("retrieve", retrieve)
builder.add_node("analyze", analyze)
builder.add_node("tools", tool_node)
builder.add_node("more_evidence", more_evidence)
builder.add_node("final_answer", final_answer)


# ============================================================
# Edges
# ============================================================

# START → Retriever
builder.add_edge(
    START,
    "retrieve",
)

# Retriever to Analyst
builder.add_edge(
    "retrieve",
    "analyze",
)

# Analyst to Tool OR evidence tool OR END
builder.add_conditional_edges(
    "analyze",
    should_continue,
    {
        "tools": "tools",
        "more_evidence": "more_evidence",
        "final_answer": "final_answer",
        END: END,
    },
)

# evidencetool to retrieve node
builder.add_edge("more_evidence", "retrieve")

# Tool to Analyst
builder.add_edge(
    "tools",
    "analyze",
)
builder.add_edge("final_answer", END)

# ============================================================
# Compile
# ============================================================
graph = builder.compile(checkpointer=memory)

logger.info("Graph built")


def run_graph(
    query: str,
    thread_id: str = "session_user_99",
    image_text: str = "",
    audio_text: str = "",
) -> str:
    if not query.strip():
        raise ValueError("Question cannot be empty.")

    multimodal_context = []

    if image_text.strip():
        multimodal_context.append(f"Text extracted from image:\n{image_text}")

    if audio_text.strip():
        multimodal_context.append(f"Text transcribed from audio:\n{audio_text}")

    if multimodal_context:
        full_query = f"User question:\n{query}\n\n" + "\n\n".join(multimodal_context)
    else:
        full_query = query

    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(
        {
            "question": full_query,
            "documents": [],
            "messages": [HumanMessage(content=full_query)],
            "tool_calls_count": 0,
        },
        config=config,
    )

    # Find the last message containing an actual answer
    for message in reversed(result["messages"]):
        content = getattr(message, "content", "")

        if isinstance(content, str) and content.strip():
            return content

    logger.error("Graph finished without generating a textual answer.")

    return "I couldn't generate an answer from the available evidence."


# while True:
#     query = input("\nEnter your question (q to quit): ").strip()

#     # Exit
#     if query.lower() == "q":
#         print("\nExiting...")
#         break

#     # Empty question
#     if not query:
#         print("Question cannot be empty.")
#         continue

#     # ========================================================
#     # Run graph
#     # ========================================================

#     result = graph.invoke(
#         {
#             "question": query,
#             "documents": [],
#             "messages": [HumanMessage(content=query)],
#             "tool_calls_count": 0,
#         },
#         config=config,
#     )
#     # ========================================================
#     # Print final answer
#     # ========================================================

#     print("\n" + "=" * 80)
#     print("FINAL ANSWER")
#     print("=" * 80)

#     final_message = result["messages"][-1]

#     print(final_message.content)

#     print("=" * 80)
