# Third Party
from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.retriever import RetrieverAgent
from src.config.prompts.analyst import ANALYST_PROMPT

# Local
from src.graph.state import AnalystState


def retrieve(state: AnalystState):

    retriever = RetrieverAgent()

    results = retriever.retrieve(
        query=state["question"],
    )

    #make sure docs have metadata and are formatted correctly
    documents = []

    for item in results:

        print("\nProcessing item:", type(item))

        if isinstance(item, tuple):
            document = item[0]
        else:
            document = item

        print("Extracted:", type(document))

        documents.append(document)

    return {
        "documents": documents
    }



def analyze_node(analyzer):

    def analyze(state: AnalystState):

        documents = state.get("documents", [])

        retrieved_info = "\n".join(
            [
                f"Source: {doc.metadata.get('source', 'Unknown')} | "
                f"Page: {doc.metadata.get('page', 'Unknown')}"
                for doc in documents
            ]
        )

        messages = [
            SystemMessage(
                content=ANALYST_PROMPT
            ),

            HumanMessage(
                content=(
                    f"Retrieved documents are available.\n"
                    f"You currently have {len(documents)} "
                    f"retrieved document chunks.\n\n"
                    f"Sources and pages:\n"
                    f"{retrieved_info}\n\n"
                    f"Question:\n"
                    f"{state['question']}"
                )
            ),

            *state["messages"],
        ]

        for i, message in enumerate(messages):
            content = str(message.content)

            print(
                f"Message {i}: "
                f"{type(message).__name__} | "
                f"{len(content):,} characters"
            )

        response = analyzer.invoke(messages)

        print("\n" + "=" * 80)
        print("ANALYST RESPONSE")
        print("=" * 80)
        print(response.content)

        print("\nTOOL CALLS:")
        for call in response.tool_calls:
            print(call)

        print("=" * 80)

        tool_calls_count = state.get(
            "tool_calls_count",
            0
        )

        if response.tool_calls:
            tool_calls_count += len(response.tool_calls)

        return {
            "messages": [response],
            "tool_calls_count": tool_calls_count,
        }

    return analyze