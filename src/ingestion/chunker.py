# Standard library

# Third-party
from langchain_core.documents import Document
from langchain_text_splitters import (
    Language,
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from loguru import logger

# Local
from src.config.settings import CHUNK_OVERLAP, CHUNK_SIZE


class Chunker:
    """
    Split documents into smaller chunks using
    format-specific strategies while preserving metadata.
    """

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
    ) -> None:

        # General-purpose splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # Python-aware splitter
        self.python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # First split Markdown according to its structure
        self.markdown_header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ],
            strip_headers=False,
        )

        # Then split large Markdown sections
        self.markdown_text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        logger.info(f"Chunker initialized (size={chunk_size}, overlap={chunk_overlap})")

    def split(
        self,
        documents: list[Document],
    ) -> list[Document]:
        """
        Select the appropriate chunking strategy based
        on the document file type.
        """

        if not documents:
            logger.warning("No documents provided for chunking.")
            return []

        file_type = (
            documents[0]
            .metadata.get(
                "file_type",
                "",
            )
            .lower()
        )

        logger.info(f"Chunking {len(documents)} document(s) of type '{file_type}'...")

        if file_type == ".md":
            return self._split_markdown(documents)

        if file_type == ".py":
            return self._split_python(documents)

        return self._split_text(documents)

    def _split_text(
        self,
        documents: list[Document],
    ) -> list[Document]:
        """
        Split general documents using recursive character splitting.

        Used for:
        - PDF
        - TXT
        - DOCX
        - PPTX
        - JSON
        - YAML
        - CSV
        """

        chunks = self.text_splitter.split_documents(documents)

        logger.success(f"Generated {len(chunks)} text chunks.")

        return chunks

    def _split_python(
        self,
        documents: list[Document],
    ) -> list[Document]:
        """
        Split Python source code using a
        proper recursive splitter.
        """

        chunks = self.python_splitter.split_documents(documents)

        logger.success(f"Generated {len(chunks)} Python chunks.")

        return chunks

    def _split_markdown(
        self,
        documents: list[Document],
    ) -> list[Document]:
        """
        Split Markdown documents in two stages:

        1. Split according to Markdown headers.
        2. Split large sections into smaller chunks.

        Header metadata and original document metadata
        are preserved.
        """

        chunks: list[Document] = []

        for document in documents:
           
            sections = self.markdown_header_splitter.split_text(document.page_content)

            for section in sections:
                
                section.metadata.update(document.metadata)

                
                section_chunks = self.markdown_text_splitter.split_documents([section])

                chunks.extend(section_chunks)

        logger.success(f"Generated {len(chunks)} Markdown chunks.")

        return chunks
