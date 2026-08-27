# Standard library
import hashlib

# Third-party
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from loguru import logger

# Local
from src.config.settings import (
    CHROMA_DB_PATH,
    COLLECTION_NAME,
)


class VectorDB:
    """
    Manage the Chroma vector database.

    Responsibilities:
    - Create or open the Chroma database.
    - Store document chunks.
    - Generate stable chunk IDs.
    - Provide access to the underlying vector store.
    """

    def __init__(
        self,
        embeddings: HuggingFaceEmbeddings,
    ) -> None:

        logger.info("Initializing Chroma Vector Database...")

        self.vector_db = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embeddings,
        )

        logger.success("Chroma Vector Database initialized.")

    def add_documents(
        self,
        documents: list[Document],
    ) -> None:
        """
        Add document chunks to Chroma.
        """

        if not documents:
            logger.warning("No documents found to add.")
            return

        logger.info(f"Adding {len(documents)} chunks to Chroma...")

        ids = self._generate_ids(documents)

        self.vector_db.add_documents(
            documents=documents,
            ids=ids,
        )

        logger.success(f"Successfully added {len(documents)} chunks.")

    def similarity_search(
        self,
        query: str,
        k: int = 5,
    ) -> list[Document]:
        """
        Perform semantic similarity search.

        This method is useful for testing and can also
        be used by the semantic search component.
        """

        logger.info(f"Performing similarity search: '{query}'")

        results = self.vector_db.similarity_search(
            query,
            k=k,
        )

        logger.success(f"Retrieved {len(results)} documents.")

        return results

    def document_count(self) -> int:
        """
        Return the number of stored chunks.
        """

        return self.vector_db._collection.count()

    def reset_database(self) -> None:
        """
        Delete the entire Chroma collection.
        """

        logger.warning("Deleting Chroma collection...")

        self.vector_db.delete_collection()

        logger.success("Chroma collection deleted.")

    def get_vector_store(self) -> Chroma:
        """
        Return the underlying Chroma vector store.
        """

        return self.vector_db

    @staticmethod
    def _generate_ids(
        documents: list[Document],
    ) -> list[str]:
        """
        Generate deterministic IDs for document chunks.

        The ID is based on:
        - source
        - page
        - chunk content

        This makes IDs reproducible when the same content
        is ingested again.
        """

        ids = []

        for index, document in enumerate(documents):
            source = document.metadata.get(
                "source",
                "unknown",
            )

            page = document.metadata.get(
                "page",
                "unknown",
            )

            content = document.page_content

            raw_id = f"{source}|{page}|{index}|{content}"

            chunk_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()

            ids.append(chunk_id)

        return ids

    def get_all_documents(self) -> list[Document]:
        """
        Return all document chunks stored in Chroma.
        """

        logger.info("Loading all documents from Chroma...")

        data = self.vector_db.get(
            include=["documents", "metadatas"],
        )

        documents = []

        for content, metadata in zip(
            data["documents"],
            data["metadatas"],
        ):
            documents.append(
                Document(
                    page_content=content,
                    metadata=metadata or {},
                )
            )

        logger.success(f"Loaded {len(documents)} documents from Chroma.")

        return documents
