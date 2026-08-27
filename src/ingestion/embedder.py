# Standard library

# Third-party
from langchain_huggingface import HuggingFaceEmbeddings
from loguru import logger

# Local
from src.config.settings import (
    EMBEDDING_DEVICE,
    EMBEDDING_MODEL_NAME,
)


class EmbeddingModel:
    """
    Initialize and manage the embedding model.
    """

    def __init__(
        self,
        model_name: str = EMBEDDING_MODEL_NAME,
        device: str = EMBEDDING_DEVICE,
    ) -> None:

        logger.info(f"Loading embedding model: {model_name} on {device}")

        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={
                "device": device,
            },
            encode_kwargs={
                "normalize_embeddings": True,
            },
        )

        logger.success("Embedding model loaded successfully.")

    def get_embeddings(self) -> HuggingFaceEmbeddings:
        """
        Return the initialized embedding model.
        """

        return self.embeddings


def main() -> None:

    logger.info("Testing Embedding Model")

    embedding_model = EmbeddingModel()

    embeddings = embedding_model.get_embeddings()

    query_vector = embeddings.embed_query("What is Retrieval-Augmented Generation?")

    print(f"Vector Dimension: {len(query_vector)}")

    print(query_vector[:10])


if __name__ == "__main__":
    main()
