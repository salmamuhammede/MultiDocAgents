# Standard library

# Third-party
from langchain_core.documents import Document
from loguru import logger

# Local


class DocumentCleaner:
    """
    Clean document text before chunking, modify page_content while preserving
    document metadata such as source, page, file_type.
    """

    def clean(
        self,
        documents: list[Document],
    ) -> list[Document]:
        """
        Clean a list of LangChain Documents.
        """

        if not documents:
            logger.warning("No documents provided for cleaning.")
            return []

        logger.info(f"Cleaning {len(documents)} document(s)...")

        cleaned_documents = []

        for document in documents:
            cleaned_text = self._clean_text(document.page_content)

            # Create a new Document so the original document is not modified.
            cleaned_document = Document(
                page_content=cleaned_text,
                metadata=document.metadata.copy(),
            )

            # Skip completely empty documents
            if cleaned_text.strip():
                cleaned_documents.append(cleaned_document)

        logger.success(
            f"Cleaning completed: {len(cleaned_documents)} document(s) remain."
        )

        return cleaned_documents

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Apply basic text normalization.
        """

        if not text:
            return ""

        logger.info("Normalize line endings")
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        logger.info("Remove null characters")
        text = text.replace("\x00", "")

        logger.info("Replace tabs with spaces")
        text = text.replace("\t", " ")

        logger.info("Remove trailing spaces from each line")
        lines = [line.rstrip() for line in text.split("\n")]

        text = "\n".join(lines)

        # Collapse excessive blank lines
        while "\n\n\n" in text:
            text = text.replace(
                "\n\n\n",
                "\n\n",
            )

        # Remove leading/trailing whitespace
        text = text.strip()

        return text
