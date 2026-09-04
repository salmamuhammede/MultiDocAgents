import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Multi Document Agents",
    page_icon="🤖",
    layout="wide",
)

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "streamlit-session"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "image_text" not in st.session_state:
    st.session_state.image_text = ""

if "audio_text" not in st.session_state:
    st.session_state.audio_text = ""


def check_api():
    """Check whether the FastAPI backend is running."""
    try:
        response = requests.get(
            f"{API_URL}/",
            timeout=5,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


def upload_document(uploaded_file):
    """Upload and index a document."""
    try:
        response = requests.post(
            f"{API_URL}/documents/upload",
            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type,
                )
            },
            timeout=300,
        )

        return response

    except requests.RequestException as e:
        st.error(f"Could not connect to API: {e}")
        return None


def extract_ocr(uploaded_file):
    """Send image to OCR endpoint."""
    try:
        response = requests.post(
            f"{API_URL}/ocr",
            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type,
                )
            },
            timeout=300,
        )

        return response

    except requests.RequestException as e:
        st.error(f"Could not connect to API: {e}")
        return None


def transcribe_audio(uploaded_file, language):
    """Send audio to Whisper endpoint."""
    try:
        response = requests.post(
            f"{API_URL}/transcribe",
            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type,
                )
            },
            data={
                "language": language,
            },
            timeout=300,
        )

        return response

    except requests.RequestException as e:
        st.error(f"Could not connect to API: {e}")
        return None


def send_chat(query, thread_id):
    """Send normal chat request."""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "query": query,
                "thread_id": thread_id,
            },
            timeout=300,
        )

        return response

    except requests.RequestException as e:
        st.error(f"Could not connect to API: {e}")
        return None


def send_multimodal_chat(
    query,
    image_text,
    audio_text,
    thread_id,
):
    """Send multimodal chat request."""
    try:
        response = requests.post(
            f"{API_URL}/chat/multimodal",
            json={
                "query": query,
                "image_text": image_text,
                "audio_text": audio_text,
                "thread_id": thread_id,
            },
            timeout=300,
        )

        return response

    except requests.RequestException as e:
        st.error(f"Could not connect to API: {e}")
        return None


with st.sidebar:
    st.title("🤖 Multi Document Agents")

    st.markdown("---")

    st.subheader("API Status")

    if check_api():
        st.success("API is running")
    else:
        st.error("API is offline")

    st.markdown("---")

    st.subheader("Session")

    st.text_input(
        "Thread ID",
        key="thread_id",
    )

    st.caption("The same Thread ID keeps the conversation context.")


st.title("🤖 Multi Document Agents")

st.markdown(
    """
    Upload documents, extract text from images,
    transcribe audio, and chat with your RAG agent.
    """
)


tab_documents, tab_chat, tab_ocr, tab_audio, tab_multimodal = st.tabs(
    [
        "📄 Documents",
        "💬 Chat",
        "🖼️ OCR",
        "🎙️ Transcription",
        "🤖 Multimodal Chat",
    ]
)


with tab_documents:
    st.header("📄 Document Upload")

    st.write(
        "Upload a supported document and it will be "
        "processed and indexed in the vector database."
    )

    document = st.file_uploader(
        "Choose a document",
        type=[
            "pdf",
            "txt",
            "md",
            "py",
            "yaml",
            "yml",
            "json",
            "csv",
            "docx",
            "pptx",
        ],
        key="document_uploader",
    )

    if document is not None:
        st.info(f"Selected: `{document.name}`")

        if st.button(
            "Upload & Index",
            type="primary",
            key="upload_document",
        ):
            with st.spinner("Uploading and indexing document..."):
                response = upload_document(document)

            if response is not None:
                if response.status_code == 200:
                    data = response.json()

                    st.success(
                        data.get(
                            "message",
                            "Document uploaded successfully.",
                        )
                    )

                    st.write(f"**Filename:** {data.get('filename')}")

                    st.write(f"**Chunks:** {data.get('message', '')}")

                else:
                    try:
                        error = response.json()
                        st.error(
                            error.get(
                                "detail",
                                "Document upload failed.",
                            )
                        )
                    except ValueError:
                        st.error(f"Upload failed: {response.text}")


with tab_chat:
    st.header("💬 RAG Chat")

    st.write("Ask questions about your indexed documents.")

    if st.button(
        "Clear Chat",
        key="clear_chat",
    ):
        st.session_state.chat_history = []
        st.rerun()

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    query = st.chat_input(
        "Ask something about your documents...",
        key="normal_chat_input",
    )

    if query:
        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": query,
            }
        )

        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = send_chat(
                    query=query,
                    thread_id=st.session_state.thread_id,
                )

            if response is not None:
                if response.status_code == 200:
                    data = response.json()

                    answer = data.get(
                        "answer",
                        "No answer returned.",
                    )

                    st.markdown(answer)

                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )

                else:
                    try:
                        error = response.json()
                        st.error(
                            error.get(
                                "detail",
                                "Chat request failed.",
                            )
                        )
                    except ValueError:
                        st.error(response.text)


with tab_ocr:
    st.header("🖼️ Image OCR")

    st.write("Upload an image and extract its text using OCR.")

    image = st.file_uploader(
        "Choose an image",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp",
        ],
        key="ocr_uploader",
    )

    if image is not None:
        st.image(
            image,
            caption=image.name,
            use_container_width=True,
        )

        if st.button(
            "Extract Text",
            type="primary",
            key="extract_ocr",
        ):
            with st.spinner("Extracting text..."):
                response = extract_ocr(image)

            if response is not None:
                if response.status_code == 200:
                    data = response.json()

                    extracted_text = data.get(
                        "text",
                        "",
                    )

                    st.session_state.image_text = extracted_text

                    st.success("Text extracted successfully.")

                    st.text_area(
                        "Extracted Text",
                        value=extracted_text,
                        height=300,
                    )

                else:
                    try:
                        error = response.json()

                        st.error(
                            error.get(
                                "detail",
                                "OCR failed.",
                            )
                        )

                    except ValueError:
                        st.error(response.text)

    elif st.session_state.image_text:
        st.text_area(
            "Previous OCR Result",
            value=st.session_state.image_text,
            height=300,
        )


with tab_audio:
    st.header("🎙️ Audio Transcription")

    st.write("Upload an audio file and select its language.")

    audio = st.file_uploader(
        "Choose an audio file",
        type=[
            "wav",
            "mp3",
            "m4a",
            "flac",
            "ogg",
        ],
        key="audio_uploader",
    )

    language = st.selectbox(
        "Audio Language",
        options=["ar", "en"],
        format_func=lambda x: "🇪🇬 Arabic" if x == "ar" else "🇬🇧 English",
    )

    if audio is not None:
        st.audio(
            audio,
            format=audio.type,
        )

        if st.button(
            "Transcribe",
            type="primary",
            key="transcribe_audio",
        ):
            with st.spinner("Transcribing audio..."):
                response = transcribe_audio(
                    audio,
                    language,
                )

            if response is not None:
                if response.status_code == 200:
                    data = response.json()

                    transcription = data.get(
                        "text",
                        "",
                    )

                    st.session_state.audio_text = transcription

                    st.success("Transcription completed.")

                    st.text_area(
                        "Transcription",
                        value=transcription,
                        height=300,
                    )

                else:
                    try:
                        error = response.json()

                        st.error(
                            error.get(
                                "detail",
                                "Transcription failed.",
                            )
                        )

                    except ValueError:
                        st.error(response.text)

    elif st.session_state.audio_text:
        st.text_area(
            "Previous Transcription",
            value=st.session_state.audio_text,
            height=300,
        )


with tab_multimodal:
    st.header("🤖 Multimodal Chat")

    st.write("Ask a question using text, an image, and/or an audio file.")

    multimodal_query = st.text_input(
        "Your Question",
        placeholder="Ask something about your documents...",
        key="multimodal_query",
    )

    st.write("Or ask your question by voice:")

    voice_question = st.audio_input(
        "🎙️ Record your question",
        key="voice_question",
    )

    st.subheader("🖼️ Image")

    multimodal_image = st.file_uploader(
        "Upload an image (optional)",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp",
        ],
        key="multimodal_image_uploader",
    )

    if multimodal_image is not None:
        st.image(
            multimodal_image,
            caption=multimodal_image.name,
            use_container_width=True,
        )

    st.subheader("🎙️ Audio")

    multimodal_audio = st.file_uploader(
        "Upload an audio file (optional)",
        type=[
            "wav",
            "mp3",
            "m4a",
            "flac",
            "ogg",
        ],
        key="multimodal_audio_uploader",
    )

    audio_language = st.selectbox(
        "Audio Language",
        options=["ar", "en"],
        format_func=lambda x: "🇪🇬 Arabic" if x == "ar" else "🇬🇧 English",
        key="multimodal_audio_language",
    )

    if multimodal_audio is not None:
        st.audio(
            multimodal_audio,
            format=multimodal_audio.type,
        )

    st.markdown("---")

    if st.button(
        "Ask Agent",
        type="primary",
        key="multimodal_submit",
    ):
        if not multimodal_query.strip() and voice_question is None:
            st.warning("Please enter or record a question.")

        else:
            query = multimodal_query.strip()

            if voice_question is not None:
                with st.spinner("🎙️ Transcribing your question..."):
                    voice_response = transcribe_audio(
                        voice_question,
                        audio_language,
                    )

                if voice_response is not None:
                    if voice_response.status_code == 200:
                        query = voice_response.json().get(
                            "text",
                            "",
                        )
                    else:
                        st.error("Voice transcription failed.")
                        st.stop()

            image_text = ""

            if multimodal_image is not None:
                with st.spinner("🔍 Extracting text from image..."):
                    ocr_response = extract_ocr(multimodal_image)

                if ocr_response is not None:
                    if ocr_response.status_code == 200:
                        image_text = ocr_response.json().get(
                            "text",
                            "",
                        )
                    else:
                        st.error("OCR failed.")
                        st.stop()

            audio_text = ""

            if multimodal_audio is not None:
                with st.spinner("🎙️ Transcribing audio evidence..."):
                    audio_response = transcribe_audio(
                        multimodal_audio,
                        audio_language,
                    )

                if audio_response is not None:
                    if audio_response.status_code == 200:
                        audio_text = audio_response.json().get(
                            "text",
                            "",
                        )
                    else:
                        st.error("Audio transcription failed.")
                        st.stop()

            with st.spinner("🤖 Agent is thinking..."):
                response = send_multimodal_chat(
                    query=query,
                    image_text=image_text,
                    audio_text=audio_text,
                    thread_id=st.session_state.thread_id,
                )

            if response is not None and response.status_code == 200:
                data = response.json()

                st.markdown("### 🤖 Agent Answer")
                st.markdown(
                    data.get(
                        "answer",
                        "No answer returned.",
                    )
                )
