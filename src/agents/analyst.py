# Third Party
from langchain_openai import ChatOpenAI

from loguru import logger

from src.config.settings import (
    ANALYST_API_KEY,
    BASE_URL,
    LLM_MODEL_NAME,
    TEMPERATURE,
)

# Local
from src.tools.calculator import Calculator
from src.tools.document_comparator import DocumentComparisonTool
from src.tools.table_extractor import extract_tables

class AnalystAgent:
    """
    Function for loading Analyst model with tools
    """

    @staticmethod
    def load_llm_with_tools():
        llm = ChatOpenAI(
            api_key=ANALYST_API_KEY,
            base_url=BASE_URL,
            model=LLM_MODEL_NAME,
            temperature=TEMPERATURE,
        )
        logger.success("Analyst model loaded.")
        calc = Calculator
        comparator = DocumentComparisonTool()
        tools = [
            calc.basic_operation,
            calc.percentage_change,
            calc.average,
            calc.statistics,
            comparator.compare_documents,
            extract_tables,
        ]
        llm_with_tools = llm.bind_tools(tools)
        logger.success("Bound tools to AnalystAgent")

        return llm_with_tools

    @staticmethod
    def get_tools():

        calc = Calculator()
        comparator = DocumentComparisonTool()

        tools = [
            calc.basic_operation,
            calc.percentage_change,
            calc.average,
            calc.statistics,
            comparator.compare_documents,
            extract_tables,
        ]

        return tools
