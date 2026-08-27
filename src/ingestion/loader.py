# Standard library
from pathlib import Path

# Third-party
from langchain_community.document_loaders import (
    CSVLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredPowerPointLoader,
)
from langchain_core.documents import Document
from loguru import logger

# Local
from src.config.settings import PDF_DOC_TEST


class SafeTextLoader(TextLoader):
    """This class to overcome error related to markdown
    that was previously notebooks

    """

    def lazy_load(self):
        logger.info("Safe Text Loader is starting ...")

        encodings = [
            "utf-8",
            "utf-8-sig",
            "cp1252",
            "latin-1",
        ]

        last_error = None

        for encoding in encodings:
            try:
                self.encoding = encoding

                yield from super().lazy_load()
                return

            except UnicodeDecodeError as e:
                last_error = e
                continue

        raise RuntimeError(f"Could not decode file: {self.file_path}") from last_error


class DocumentLoader:
    """Load supported document types into LangChain Documents."""

    def __init__(self) -> None:
        logger.info("Document Loader is starting ...")
        self.loader_mapping = {
            ".pdf": PyPDFLoader,
            ".txt": SafeTextLoader,
            ".md": SafeTextLoader,
            ".py": SafeTextLoader,
            ".yaml": SafeTextLoader,
            ".yml": SafeTextLoader,
            ".json": SafeTextLoader,
            ".csv": CSVLoader,
            ".docx": Docx2txtLoader,
            ".pptx": UnstructuredPowerPointLoader,
        }

    def load(self, source: str) -> list[Document]:
        """Load a document based on its file extension."""

        extension = Path(source).suffix.lower()

        loader_class = self.loader_mapping.get(extension)

        if loader_class is None:
            raise ValueError(f"Unsupported file type: {extension}")

        logger.info(f"Loading document: {source}")

        loader = loader_class(source)
        documents = loader.load()

        for document in documents:
            document.metadata["file_type"] = extension
            document.metadata["source"] = source

        logger.success(f"Loaded {len(documents)} document(s)")

        return documents

    @staticmethod
    def print_document_info(
        documents: list[Document],
    ) -> None:
        """
        Print basic information about loaded documents.
        """

        print(f"Documents: {len(documents)}")

        print("-" * 50)

        print(documents[0].page_content)

        print("-" * 50)

        print(documents[0].metadata)


def main() -> None:

    logger.info("Testing Document Loader")

    loader = DocumentLoader()

    documents = loader.load(PDF_DOC_TEST)
    loader.print_document_info(documents)


if __name__ == "__main__":
    main()
