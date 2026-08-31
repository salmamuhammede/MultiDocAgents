# Third Party
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage


from src.agents.analyst import AnalystAgent
from src.agents.retriever import RetrieverAgent

# Local
from src.graph.state import AnalystState
from src.config.prompts.analyst import ANALYST_PROMPT

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

        messages = [
        SystemMessage(content=ANALYST_PROMPT),
        *state["messages"],
    ]
        response = analyzer.invoke(messages)

        return {
            "messages": [response]
        }

    return analyze