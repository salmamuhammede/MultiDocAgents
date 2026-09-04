# Standard library
from pathlib import Path

# Third-party
from faster_whisper import WhisperModel
from loguru import logger

# Local
from src.config.settings import AUDIO_TEST_PATH, WHISPER_COMPUTE_TYPE, WHISPER_MODEL


class WhisperService:
    """
    This class is responsible for converting speech into text
    using the Faster-Whisper model to support user audio feature.
    """

    def __init__(
        self,
        model_name: str = WHISPER_MODEL,
        compute_type: str = WHISPER_COMPUTE_TYPE,
    ):
        """
        Initialize the Faster-Whisper model.

        Args:
            model_name: Faster-Whisper model size.
            compute_type: Computation type used by the model.
        """
        logger.info(f"Loading Faster-Whisper model: {model_name}")

        self.model = WhisperModel(
            model_name,
            device="cpu",
            compute_type=compute_type,
        )

        logger.success("Faster-Whisper model loaded successfully.")

    def transcribe(
        self,
        audio_path: str | Path,
        language: str | None = "en",
    ) -> str:
        """
        Transcribe an audio file into text to extract user voice query.

        Args:
            audio_path (str | Path): Path to the audio file.
            language (str | None): Optional language code such as 'en' or 'ar'.

        Returns:
            transcription (str): Transcribed text.
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            logger.error(f"Audio file not found: {audio_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Starting transcription: {audio_path.name}")

        segments, info = self.model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
        )

        transcription = " ".join(segment.text.strip() for segment in segments).strip()

        logger.success(f"Transcription completed. Detected language: {info.language}")

        return transcription


def main():
    logger.info("Testing Audio Module ....")
    service = WhisperService()

    audio_path = AUDIO_TEST_PATH

    transcription = service.transcribe(
        audio_path,
        language="ar",
    )

    print("Transcription:\n")
    print(transcription)


if __name__ == "__main__":
    main()
