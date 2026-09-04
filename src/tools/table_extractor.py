# Third Party

import json
from pathlib import Path
from typing import Annotated, Any

import pdfplumber
from langchain_core.documents import Document
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from loguru import logger

# ============================================================
# Configuration
# ============================================================

NEARBY_PAGE_RANGE = 2


# ============================================================
# Page Utilities
# ============================================================


def _normalize_page_number(page: Any) -> int:
    """
    Convert 0-based page metadata into a 1-based PDF page number.

    Example:
        Retriever page 0 -> PDF page 1
        Retriever page 8 -> PDF page 9
    """

    try:
        page = int(page)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid page number: {page}")

    if page >= 0:
        return page + 1

    return page


def _get_nearby_pages(
    page_number: int,
    total_pages: int,
    page_range: int = NEARBY_PAGE_RANGE,
) -> list[int]:
    """
    Return the target page and nearby pages.

    Example:
        page_number = 8
        page_range = 2

        Returns:
        [6, 7, 8, 9, 10]

    Page numbers are 1-based.
    """

    start_page = max(1, page_number - page_range)
    end_page = min(total_pages, page_number + page_range)

    return list(range(start_page, end_page + 1))


# ============================================================
# Table Extraction
# ============================================================


def _find_tables_on_page(
    pdf: pdfplumber.PDF,
    page_number: int,
) -> list[list[list[str]]]:
    """
    Extract all tables from a specific page.

    pdfplumber pages are accessed using 0-based indexes,
    while page_number is 1-based.
    """

    if page_number < 1 or page_number > len(pdf.pages):
        return []

    logger.info(f"Opening page for table extraction: Page {page_number}")

    page = pdf.pages[page_number - 1]

    extracted_tables = page.extract_tables()

    tables = []

    for table in extracted_tables:
        if table:
            tables.append(table)

    return tables


# ============================================================
# Table Cleaning
# ============================================================


def _clean_table(
    table: list[list[Any]],
) -> list[list[str]]:
    """
    Clean cells and remove completely empty rows.
    """

    cleaned = []

    for row in table:
        if row is None:
            continue

        cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]

        if any(cell != "" for cell in cleaned_row):
            cleaned.append(cleaned_row)

    return cleaned


# ============================================================
# Convert Table to Records
# ============================================================


def _table_to_records(
    table: list[list[str]],
) -> dict[str, Any]:
    """
    Convert a raw table into a structured representation.

    Assumes the first row contains the headers.
    """

    if not table:
        return {
            "columns": [],
            "rows": [],
        }

    headers = table[0]

    normalized_headers = []

    for i, header in enumerate(headers):
        header = header.strip()

        if not header:
            header = f"column_{i + 1}"

        normalized_headers.append(header)

    rows = []

    for row in table[1:]:
        if len(row) < len(normalized_headers):
            row = row + [""] * (len(normalized_headers) - len(row))

        elif len(row) > len(normalized_headers):
            row = row[: len(normalized_headers)]

        record = {normalized_headers[i]: row[i] for i in range(len(normalized_headers))}

        rows.append(record)

    return {
        "columns": normalized_headers,
        "rows": rows,
    }


# ============================================================
# Table Extractor Tool
# ============================================================


@tool
def extract_tables(
    question: str,
    documents: Annotated[
        list[Document],
        InjectedState("documents"),
    ],
) -> str:
    """
    Extract structured tables from pages relevant to the
    current question and from nearby pages.

    For every page retrieved by the retriever, this tool also
    checks nearby pages within NEARBY_PAGE_RANGE.

    Example:
        If the retriever returns page 8 and the nearby page
        range is 2, pages 6-10 will be inspected.

    The tool returns structured tables containing:
        - source
        - page
        - table ID
        - columns
        - rows
    """

    logger.info("Called table extractor tool")

    extracted_tables = []

    # Prevent the same source/page from being processed
    # multiple times.
    processed_pages = set()

    # --------------------------------------------------------
    # First determine all nearby pages
    # --------------------------------------------------------

    pages_to_process = []

    for document in documents:
        metadata = document.metadata or {}

        source = metadata.get("source")
        page = metadata.get("page")

        if not source or page is None:
            continue

        source = str(source)

        pdf_path = Path(source)

        if not pdf_path.exists():
            logger.warning(f"PDF does not exist: {pdf_path}")
            continue

        try:
            retrieved_page = _normalize_page_number(page)

        except ValueError:
            logger.warning(f"Invalid page metadata: {page}")
            continue

        # ----------------------------------------------------
        # Open PDF once to determine total number of pages
        # ----------------------------------------------------

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)

                nearby_pages = _get_nearby_pages(
                    retrieved_page,
                    total_pages,
                    NEARBY_PAGE_RANGE,
                )

        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to inspect PDF {source}: {e}")

            continue

        # ----------------------------------------------------
        # Add nearby pages
        # ----------------------------------------------------

        for page_number in nearby_pages:
            pages_to_process.append(
                (
                    str(pdf_path),
                    page_number,
                    retrieved_page,
                )
            )

    # --------------------------------------------------------
    # Extract tables
    # --------------------------------------------------------

    for source, page_number, retrieved_page in pages_to_process:
        page_key = (
            str(Path(source).resolve()),
            page_number,
        )

        if page_key in processed_pages:
            continue

        processed_pages.add(page_key)

        logger.info(f"Checking page {page_number} (retrieved page: {retrieved_page})")

        try:
            with pdfplumber.open(source) as pdf:
                raw_tables = _find_tables_on_page(
                    pdf,
                    page_number,
                )

        except Exception as e:  # noqa: BLE001
            logger.error(
                f"Failed to extract tables from {source} page {page_number}: {e}"
            )

            extracted_tables.append(
                {
                    "source": source,
                    "page": page_number,
                    "error": f"Failed to extract tables: {e!s}",
                }
            )

            continue

        # ----------------------------------------------------
        # Process extracted tables
        # ----------------------------------------------------

        for table_index, raw_table in enumerate(raw_tables):
            cleaned_table = _clean_table(raw_table)

            if not cleaned_table:
                continue

            structured_table = _table_to_records(cleaned_table)

            logger.info(f"Extracted table from {Path(source).name} page {page_number}")

            extracted_tables.append(
                {
                    "table_id": (f"table_{len(extracted_tables) + 1}"),
                    "source": source,
                    "page": page_number,
                    "retrieved_from_page": retrieved_page,
                    "table_index": table_index,
                    "columns": structured_table["columns"],
                    "rows": structured_table["rows"],
                }
            )

    # --------------------------------------------------------
    # No tables
    # --------------------------------------------------------

    if not extracted_tables:
        logger.info("Found no tables")

        return json.dumps(
            {
                "question": question,
                "tables_found": 0,
                "tables": [],
            },
            indent=2,
        )

    # --------------------------------------------------------
    # Return tables
    # --------------------------------------------------------

    logger.info(f"Found {len(extracted_tables)} tables")

    return json.dumps(
        {
            "question": question,
            "tables_found": len(extracted_tables),
            "nearby_page_range": NEARBY_PAGE_RANGE,
            "tables": extracted_tables,
        },
        indent=2,
    )
