#Third Party
from typing import List, Dict, Any, Annotated
from pathlib import Path
import json
import pdfplumber
from langchain_core.documents import Document
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from loguru import logger


def _normalize_page_number(page: Any) -> int:
    """
    Convert page metadata into a 1-based PDF page number.

    Most PDF libraries use 0-based indexes internally, while
    pdfplumber uses 1-based page access.
    """

    try:
        page = int(page)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid page number: {page}")

     # If Result 4 says Page 0, it actually maps to the 1st page of the PDF.
    if page >= 0:
        return page + 1
    return page


def _find_tables_on_page(pdf_path: str, page_number: int) -> List[List[List[str]]]:
    """
    Extract all tables from a specific PDF page.
    """

    tables = []
    logger.info(f"Opening file to find tables: {Path(pdf_path).resolve()} (Page: {page_number})")
    with pdfplumber.open(pdf_path) as pdf:

        if page_number < 1 or page_number > len(pdf.pages):
            return []

        page = pdf.pages[page_number - 1]

        extracted_tables = page.extract_tables()

        for table in extracted_tables:
            if table:
                tables.append(table)

    return tables


def _clean_table(table: List[List[Any]]) -> List[List[str]]:
    """
    Clean cells and remove completely empty rows.
    """

    cleaned = []

    for row in table:

        if row is None:
            continue

        cleaned_row = [
            str(cell).strip() if cell is not None else ""
            for cell in row
        ]

        # Ignore completely empty rows
        if any(cell != "" for cell in cleaned_row):
            cleaned.append(cleaned_row)

    return cleaned


def _table_to_records(table: List[List[str]]) -> Dict[str, Any]:
    """
    Convert a raw table into a structured representation.

    Assumes the first row is the header.
    """

    if not table:
        return {
            "columns": [],
            "rows": []
        }

    headers = table[0]

    # Handle duplicate/empty column names
    normalized_headers = []

    for i, header in enumerate(headers):
        header = header.strip()

        if not header:
            header = f"column_{i + 1}"

        normalized_headers.append(header)

    rows = []

    for row in table[1:]:

        # Make row length match number of columns
        if len(row) < len(normalized_headers):
            row = row + [""] * (len(normalized_headers) - len(row))

        elif len(row) > len(normalized_headers):
            row = row[:len(normalized_headers)]

        record = {
            normalized_headers[i]: row[i]
            for i in range(len(normalized_headers))
        }

        rows.append(record)

    return {
        "columns": normalized_headers,
        "rows": rows
    }


@tool
def extract_tables(
    question: str,
    documents: Annotated[List[Document], InjectedState("documents")]
) -> str:
    """
    Extract structured tables from the document pages relevant to the
    current question.

    The documents come from the retriever through LangGraph state.

    The tool uses the source file and page metadata to locate the original
    PDF and extract tables from the relevant pages.

    Returns structured tables containing source, page, columns and rows.
    """
    logger.info("Called table extractor tool")
    extracted_tables = []

    # Avoid extracting the same PDF page multiple times because
    # several retrieved chunks can come from the same page.
    processed_pages = set()

    for document in documents:

        metadata = document.metadata or {}

        source = metadata.get("source")
        page = metadata.get("page")

        if not source or page is None:
            continue

        source = str(source)

        # Normalize path
        pdf_path = Path(source)

        if not pdf_path.exists():
            continue

        try:
            page_number = _normalize_page_number(page)

        except ValueError:
            continue

        page_key = (str(pdf_path.resolve()), page_number)

        if page_key in processed_pages:
            continue

        processed_pages.add(page_key)

        try:
            raw_tables = _find_tables_on_page(
                str(pdf_path),
                page_number
            )

        except Exception as e:
            extracted_tables.append({
                "source": source,
                "page": page_number,
                "error": f"Failed to extract tables: {str(e)}"
            })
            continue

        for table_index, raw_table in enumerate(raw_tables):

            cleaned_table = _clean_table(raw_table)

            if not cleaned_table:
                continue

            structured_table = _table_to_records(cleaned_table)
            logger.info("Extracting tables")
            extracted_tables.append({
                "table_id": f"table_{len(extracted_tables) + 1}",
                "source": source,
                "page": page_number,
                "table_index": table_index,
                "columns": structured_table["columns"],
                "rows": structured_table["rows"]
            })

    if not extracted_tables:
        logger.info("Found no tables")
        return json.dumps(
            {
                "question": question,
                "tables_found": 0,
                "tables": []
            },
            indent=2
        )

    return json.dumps(
        {
            "question": question,
            "tables_found": len(extracted_tables),
            "tables": extracted_tables
        },
        indent=2
    )