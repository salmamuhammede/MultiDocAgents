# Standard library
from pathlib import Path

# Third-party
from loguru import logger

from src.config.settings import PDF_DOC_TEST

# Local
from src.ingestion.chunker import Chunker
from src.ingestion.cleaner import DocumentCleaner
from src.ingestion.embedder import EmbeddingModel
from src.ingestion.loader import DocumentLoader
from src.retrieval.vector_store import VectorDB


class IngestionPipeline:
    """
    Orchestrates the document ingestion pipeline either online or offline.

    Flow:
        Load → Clean → Chunk → Store
    """

    def __init__(
        self,
        loader: DocumentLoader | None = None,
        cleaner: DocumentCleaner | None = None,
        chunker: Chunker | None = None,
        vector_db: VectorDB | None = None,
    ) -> None:

        self.loader = loader or DocumentLoader()

        self.cleaner = cleaner or DocumentCleaner()

        self.chunker = chunker or Chunker()

        if vector_db is None:
            embeddings = EmbeddingModel().get_embeddings()
            self.vector_db = VectorDB(embeddings)
        else:
            self.vector_db = vector_db

        logger.info("Ingestion pipeline initialized.")

    def process(
        self,
        source: str,
    ) -> int:
        """
        Process a single document.

        Flow:
            Load → Clean → Chunk → Store

        Returns:
            Number of chunks stored.
        """

        logger.info(f"Starting ingestion: {source}")

        # 1. Load
        documents = self.loader.load(source)

        logger.info(f"[load] Loaded {len(documents)} document(s)")

        # 2. Clean
        documents = self.cleaner.clean(documents)

        logger.info(f"[clean] {len(documents)} document(s) remain")

        if not documents:
            logger.warning(f"No content remaining after cleaning: {source}")
            return 0

        # 3. Chunk
        chunks = self.chunker.split(documents)

        logger.info(f"[chunk] Generated {len(chunks)} chunk(s)")

        if not chunks:
            logger.warning(f"No chunks generated: {source}")
            return 0

        # 4. Store
        self.vector_db.add_documents(chunks)

        logger.success(f"[store] Stored {len(chunks)} chunk(s)")

        return len(chunks)

    def process_directory(
        self,
        folder_path: str,
    ) -> int:
        """
        Process all supported documents inside a directory.
        """

        folder = Path(folder_path)

        if not folder.exists():
            raise FileNotFoundError(f"Folder does not exist: {folder_path}")

        if not folder.is_dir():
            raise ValueError(f"Path is not a directory: {folder_path}")

        supported_extensions = {
            ".pdf",
            ".txt",
            ".md",
            ".py",
            ".yaml",
            ".yml",
            ".json",
            ".csv",
            ".docx",
            ".pptx",      
        }

        files = [
            path
            for path in folder.rglob("*")
            if (path.is_file() and path.suffix.lower() in supported_extensions)
        ]

        if not files:
            logger.warning(f"No supported documents found in {folder_path}")
            return 0

        logger.info(f"Found {len(files)} document(s)")

        total_chunks = 0

        for file_path in files:
            try:
                chunks_count = self.process(str(file_path))
                total_chunks += chunks_count

            except (FileNotFoundError, ValueError, RuntimeError, OSError) as e:
                logger.error(f"Failed to process {file_path}: {e}")

        logger.success(f"Directory ingestion completed. Total chunks: {total_chunks}")

        return total_chunks


def main() -> None:
    """
    Test the ingestion pipeline on a single document.
    """

    logger.info("Testing Ingestion Pipeline")

    
    source = PDF_DOC_TEST

    pipeline = IngestionPipeline()

    chunks_count = pipeline.process(source)

    print("\n" + "=" * 60)
    print("INGESTION RESULT")
    print("=" * 60)

    print(f"Source: {source}")
    print(f"Chunks stored: {chunks_count}")
    print(f"Total chunks in Vector DB: {pipeline.vector_db.document_count()}")


if __name__ == "__main__":
    main()
