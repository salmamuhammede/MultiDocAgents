#Third party
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from loguru import logger

#Local
from src.agents.analyst import AnalystAgent
from src.config.settings import (
    MAX_TOOL_CALLS,
)
from src.graph.nodes import analyze_node, more_evidence, retrieve
from src.graph.state import AnalystState

# ============================================================
# Create tools
# ============================================================

#initialize analyzer once
analyst = AnalystAgent.load_llm_with_tools()

#instantiate memory
memory = MemorySaver()

tools = AnalystAgent.get_tools()

tool_node = ToolNode(tools)

analyze = analyze_node(analyst)


# ============================================================
# Decide whether Analyst wants to use a tool
# ============================================================

def should_continue(state):

    if state.get("tool_calls_count", 0) >= MAX_TOOL_CALLS:
        return END

    last_message = state["messages"][-1]

    tool_calls = getattr(last_message, "tool_calls", [])

    if not tool_calls:
        return END

    for call in tool_calls:

        if call["name"] == "search_more_evidence":
            return "more_evidence"

    return "tools"

# ============================================================
# Build graph
# ============================================================

builder = StateGraph(AnalystState)

# Nodes
builder.add_node("retrieve", retrieve)
builder.add_node("analyze", analyze)
builder.add_node("tools", tool_node)
builder.add_node("more_evidence",more_evidence)


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

# Analyst to Tool OR evidencetool OR END
builder.add_conditional_edges(
    "analyze",
    should_continue,
    {
        "tools": "tools",
        "more_evidence": "more_evidence",
        END: END,
    },
)

#evidencetool to retrieve node
builder.add_edge(
    "more_evidence",
    "retrieve"
)

# Tool to Analyst
builder.add_edge(
    "tools",
    "analyze",
)


# ============================================================
# Compile
# ============================================================
graph = builder.compile(checkpointer=memory)

logger.info("Graph built")

config = {"configurable": {"thread_id": "session_user_99"}}


while True:

    query = input("\nEnter your question (q to quit): ").strip()

    # Exit
    if query.lower() == "q":
        print("\nExiting...")
        break

    # Empty question
    if not query:
        print("Question cannot be empty.")
        continue

    # ========================================================
    # Run graph
    # ========================================================

    result = graph.invoke(
    {
        "question": query,
        "documents": [],
        "messages": [
            HumanMessage(content=query)
        ],
        "tool_calls_count": 0,
    },
    config=config
)
    # ========================================================
    # Print final answer
    # ========================================================

    print("\n" + "=" * 80)
    print("FINAL ANSWER")
    print("=" * 80)

    final_message = result["messages"][-1]

    print(final_message.content)

    print("=" * 80)