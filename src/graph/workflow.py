from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from loguru import logger

from src.graph.nodes import analyze_node, retrieve
from src.graph.state import AnalystState
from langchain_core.messages import HumanMessage
#Local
from src.agents.analyst import AnalystAgent

# ============================================================
# Create tools
# ============================================================

#initialize analyzer once
analyst = AnalystAgent.load_llm_with_tools()

tools = AnalystAgent.get_tools()

tool_node = ToolNode(tools)

analyze = analyze_node(analyst)


# ============================================================
# Decide whether Analyst wants to use a tool
# ============================================================

def should_continue(state: AnalystState):

    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return END

# ============================================================
# Build graph
# ============================================================

builder = StateGraph(AnalystState)

# Nodes
builder.add_node("retrieve", retrieve)
builder.add_node("analyze", analyze)
builder.add_node("tools", tool_node)


# ============================================================
# Edges
# ============================================================

# START → Retriever
builder.add_edge(
    START,
    "retrieve",
)

# Retriever → Analyst
builder.add_edge(
    "retrieve",
    "analyze",
)

# Analyst → Tool OR END
builder.add_conditional_edges(
    "analyze",
    should_continue,
    {
        "tools": "tools",
        END: END,
    },
)

# Tool → Analyst
builder.add_edge(
    "tools",
    "analyze",
)


# ============================================================
# Compile
# ============================================================

graph = builder.compile()

logger.info("Graph built")

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
                HumanMessage(
                    content=query
                )
            ],
        }
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