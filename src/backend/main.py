# Standard library
from pathlib import Path
from typing import Literal
from uuid import uuid4

# Third-party
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

load_dotenv()

# Local
from src.additional_features_task2.ocr.ocr_feature import OCRService
from src.additional_features_task2.voice.voice_feature import WhisperService
from src.config.settings import AUDIO_UPLOADS_FOLDER, IMAGES_UPLOADS_FOLDER, UPLOAD_DIR
from src.graph.workflow import run_graph
from src.ingestion.pipeline import IngestionPipeline

app = FastAPI(
    title="Multi Document Agents API",
    description="API for multi-document RAG, OCR, Voice, and LangGraph agents",
    version="1.0.0",
)

DOCUMENT_UPLOADS_FOLDER = UPLOAD_DIR

Path(DOCUMENT_UPLOADS_FOLDER).mkdir(
    parents=True,
    exist_ok=True,
)

Path(AUDIO_UPLOADS_FOLDER).mkdir(
    parents=True,
    exist_ok=True,
)

Path(IMAGES_UPLOADS_FOLDER).mkdir(
    parents=True,
    exist_ok=True,
)

SUPPORTED_DOCUMENT_EXTENSIONS = {
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

SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

SUPPORTED_AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".flac",
    ".ogg",
}

ocr_service = OCRService(languages=["en"])

whisper_service = WhisperService()

ingestion_pipeline = IngestionPipeline()


class ChatRequest(BaseModel):
    """
    Request for normal text-based chat.
    """

    query: str = Field(
        ...,
        min_length=1,
        description="User question",
    )

    thread_id: str = Field(
        ...,
        min_length=1,
        description="Conversation/session ID",
    )


class MultiModalChatRequest(BaseModel):
    """
    Request containing the user query plus
    optional OCR and audio transcription text.
    """

    query: str = Field(
        ...,
        min_length=1,
        description="User question",
    )

    image_text: str = Field(
        default="",
        description="Text extracted from an image using OCR",
    )

    audio_text: str = Field(
        default="",
        description="Text transcribed from audio using Whisper",
    )

    thread_id: str = Field(
        ...,
        min_length=1,
        description="Conversation/session ID",
    )


class ChatResponse(BaseModel):
    """
    Standard response returned by the agent.
    """

    answer: str

    thread_id: str


class UploadResponse(BaseModel):
    """
    Response returned after uploading a document.
    """

    message: str

    filename: str

    file_path: str


class OCRResponse(BaseModel):
    """
    OCR result.
    """

    text: str

    filename: str


class TranscriptionResponse(BaseModel):
    """
    Whisper transcription result.
    """

    text: str

    filename: str


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Multi Document Agents API is running",
    }


@app.post(
    "/documents/upload",
    response_model=UploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),  # noqa: B008
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is missing.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in SUPPORTED_DOCUMENT_EXTENSIONS:
        supported_formats = ", ".join(
            sorted(SUPPORTED_DOCUMENT_EXTENSIONS),
        )

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported document format. Supported formats: {supported_formats}"
            ),
        )

    file_id = uuid4()

    safe_filename = f"{file_id}_{Path(file.filename).name}"

    file_path = Path(DOCUMENT_UPLOADS_FOLDER) / safe_filename

    content = await file.read()

    file_path.write_bytes(content)

    try:
        chunks_count = ingestion_pipeline.process(
            str(file_path),
        )

        return UploadResponse(
            message=(
                "Document uploaded and indexed successfully. "
                f"Created {chunks_count} chunk(s)."
            ),
            filename=file.filename,
            file_path=str(file_path),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document ingestion error: {e!s}",
        ) from e


@app.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
):
    try:
        answer = run_graph(
            query=request.query,
            thread_id=request.thread_id,
        )

        return ChatResponse(
            answer=answer,
            thread_id=request.thread_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {e!s}",
        ) from e


@app.post(
    "/ocr",
    response_model=OCRResponse,
)
async def extract_text_from_image(
    file: UploadFile = File(...),  # noqa: B008
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is missing.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in SUPPORTED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=("Unsupported image format. Use PNG, JPG, JPEG, or WEBP."),
        )

    file_id = uuid4()

    safe_filename = f"{file_id}_{Path(file.filename).name}"

    image_path = Path(IMAGES_UPLOADS_FOLDER) / safe_filename

    content = await file.read()

    image_path.write_bytes(content)

    try:
        extracted_text = ocr_service.extract_text(
            image_path,
        )

        return OCRResponse(
            text=extracted_text,
            filename=file.filename,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR error: {e!s}",
        ) from e


@app.post(
    "/transcribe",
    response_model=TranscriptionResponse,
)
async def transcribe_audio(
    file: UploadFile = File(...),  # noqa: B008
    language: Literal["ar", "en"] = Form(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is missing.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in SUPPORTED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=("Unsupported audio format. Use WAV, MP3, M4A, FLAC, or OGG."),
        )

    file_id = uuid4()

    safe_filename = f"{file_id}_{Path(file.filename).name}"

    audio_path = Path(AUDIO_UPLOADS_FOLDER) / safe_filename

    content = await file.read()

    audio_path.write_bytes(content)

    try:
        transcription = whisper_service.transcribe(
            audio_path,
            language=language,
        )

        return TranscriptionResponse(
            text=transcription,
            filename=file.filename,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription error: {e!s}",
        ) from e


@app.post(
    "/chat/multimodal",
    response_model=ChatResponse,
)
def multimodal_chat(
    request: MultiModalChatRequest,
):
    try:
        answer = run_graph(
            query=request.query,
            image_text=request.image_text,
            audio_text=request.audio_text,
            thread_id=request.thread_id,
        )

        return ChatResponse(
            answer=answer,
            thread_id=request.thread_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {e!s}",
        ) from e
