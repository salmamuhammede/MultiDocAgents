# Third Party
from langchain_core.messages import HumanMessage

from src.agents.analyst import AnalystAgent
from src.agents.retriever import RetrieverAgent

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

    print("\n" + "=" * 80)
    print("DOCUMENTS SENT TO STATE")
    print("=" * 80)

    for i, document in enumerate(documents):
        print(f"\nDocument {i}")
        print("Type:", type(document))
        print("Has metadata:", hasattr(document, "metadata"))
        print("Has page_content:", hasattr(document, "page_content"))

    print("=" * 80)

    return {
        "documents": documents
    }


from src.graph.state import AnalystState


def analyze_node(analyzer):

    def analyze(state: AnalystState):

        response = analyzer.invoke(
            state["messages"]
        )

        return {
            "messages": [response]
        }

    return analyze