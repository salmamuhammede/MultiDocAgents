from langchain_core.documents import Document
from loguru import logger


class ContextSelector:
    """
    Select the most useful and diverse documents from
    reranked retrieval results.

    Responsibilities:
    - Keep the highest-ranked documents.
    - Remove highly similar/duplicate chunks.
    - Respect the maximum number of chunks.
    - Respect the maximum context length.
    - Preserve document metadata for citations.
    """

    def __init__(
        self,
        max_chunks: int = 5,
        max_context_chars: int = 12000,
        similarity_threshold: float = 0.90,
    ) -> None:

        if max_chunks <= 0:
            raise ValueError("max_chunks must be greater than 0.")

        if max_context_chars <= 0:
            raise ValueError("max_context_chars must be greater than 0.")

        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError("similarity_threshold must be between 0 and 1.")

        self.max_chunks = max_chunks
        self.max_context_chars = max_context_chars
        self.similarity_threshold = similarity_threshold

    def select(
        self,
        reranked_documents: list[tuple[Document, float]],
    ) -> list[tuple[Document, float]]:
        """
        Select the final context from reranked documents.

        Args:
            reranked_documents:
                Documents returned by the reranker as
                (Document, relevance_score).

        Returns:
            Selected documents with their relevance scores.
        """

        if not reranked_documents:
            logger.warning("No documents provided to ContextSelector.")
            return []

        selected: list[tuple[Document, float]] = []
        current_context_length = 0

        for document, score in reranked_documents:
            if len(selected) >= self.max_chunks:
                break

            content = document.page_content.strip()

            if not content:
                continue

            # Avoid duplicate or highly overlapping chunks
            if self._is_redundant(
                document,
                selected,
            ):
                continue

            content_length = len(content)

            # Respect maximum context size
            if current_context_length + content_length > self.max_context_chars:
                logger.debug(
                    "Skipping document because maximum context length was reached."
                )
                continue

            selected.append(
                (
                    document,
                    score,
                )
            )

            current_context_length += content_length

        logger.success(
            f"Context selection: {len(reranked_documents)} → {len(selected)} chunks"
        )

        return selected

    def _is_redundant(
        self,
        document: Document,
        selected_documents: list[tuple[Document, float]],
    ) -> bool:
        """
        Check whether a document is too similar to an
        already selected document.

        The initial implementation uses token overlap.
        """

        if not selected_documents:
            return False

        current_tokens = self._tokenize(document.page_content)

        if not current_tokens:
            return True

        for selected_document, _ in selected_documents:
            selected_tokens = self._tokenize(selected_document.page_content)

            similarity = self._jaccard_similarity(
                current_tokens,
                selected_tokens,
            )

            if similarity >= self.similarity_threshold:
                return True

        return False

    @staticmethod
    def _tokenize(
        text: str,
    ) -> set[str]:
        """
        Convert text into a set of normalized tokens.
        """

        return {
            token.strip(".,!?;:()[]{}\"'")
            for token in text.lower().split()
            if token.strip(".,!?;:()[]{}\"'")
        }

    @staticmethod
    def _jaccard_similarity(
        tokens_a: set[str],
        tokens_b: set[str],
    ) -> float:
        """
        Calculate Jaccard similarity between two token sets.
        """

        if not tokens_a or not tokens_b:
            return 0.0

        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)

        return len(intersection) / len(union)
