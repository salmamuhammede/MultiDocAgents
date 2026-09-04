# Standard library
from pathlib import Path

# Third-party
import cv2
import easyocr
from loguru import logger

# Local
from src.config.settings import IMAGE_TEST_PATH


class OCRService:
    """
    This class is responsible for extracting text from images
    using EasyOCR to support ocr feature in task 2.
    """

    def __init__(self, languages: list[str] | None = None):
        """
        Initialize the OCR reader.

        Args:
            languages: Languages to recognize, allowed ones ["en"] or ["en", "ar"].
        """
        if languages is None:
            languages = ["en"]

        logger.info(f"Loading OCR model for languages: {languages}")

        self.reader = easyocr.Reader(
            languages,
            gpu=False,
        )

        logger.success("OCR model loaded successfully.")

    def extract_text(self, image_path: str | Path) -> str:
        """
        Extract text from an image.

        Args:
            image_path: Path to the input image.

        Returns:
            Extracted text.
        """
        image_path = Path(image_path)

        if not image_path.exists():
            logger.error(f"Image file not found: {image_path}")
            raise FileNotFoundError(f"Image file not found: {image_path}")

        logger.info(f"Starting OCR: {image_path.name}")

        # Read the image using OpenCV
        image = cv2.imread(
            str(image_path),
            cv2.IMREAD_COLOR,
        )

        if image is None:
            logger.error(f"Could not read image: {image_path}")
            raise ValueError(f"Could not read image: {image_path}")

        # to make sure the image has the correct datatype
        if image.dtype != "uint8":
            image = image.astype("uint8")

        logger.info(
            f"Image loaded successfully: shape={image.shape}, dtype={image.dtype}"
        )

        # Run OCR
        results = self.reader.readtext(
            image,
            detail=0,
        )

        extracted_text = " ".join(results).strip()

        logger.success("OCR completed successfully.")

        return extracted_text


def main():
    logger.info("Testing Ocr module ...")
    ocr_service = OCRService(languages=["en"])

    image_path = IMAGE_TEST_PATH

    text = ocr_service.extract_text(image_path)

    print("\nExtracted text:")
    print(text)


if __name__ == "__main__":
    main()
