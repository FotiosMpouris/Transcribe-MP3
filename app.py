import streamlit as st
from openai import OpenAI
import os
import io
from pydub import AudioSegment
from pydub.utils import make_chunks
import math

# --- Constants ---
OPENAI_API_FILE_LIMIT_MB = 25
OPENAI_API_FILE_LIMIT_BYTES = OPENAI_API_FILE_LIMIT_MB * 1024 * 1024
# Target slightly less for chunks to be safe with overhead
TARGET_CHUNK_SIZE_BYTES = (OPENAI_API_FILE_LIMIT_MB - 1) * 1024 * 1024


# --- Helper Function ---
def transcribe_audio_chunk(client, audio_chunk_bytesio, attempt=1, max_attempts=3):
    """
    Transcribes a single audio chunk (BytesIO object) using OpenAI's Whisper API.
    Includes basic retry logic for transient errors.
    """
    try:
        audio_chunk_bytesio.seek(0) # Ensure pointer is at the beginning
        # When passing a file object, OpenAI SDK needs a name.
        # It doesn't have to be the original, just a placeholder.
        # We also need to tell it the type.
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio_chunk.mp3", audio_chunk_bytesio, "audio/mpeg"), # Pass as a tuple
            response_format="text"
        )
        return transcript
    except Exception as e:
        st.warning(f"Error transcribing chunk (attempt {attempt}/{max_attempts}): {e}")
        if attempt < max_attempts:
            st.info(f"Retrying chunk transcription ({attempt+1}/{max_attempts})...")
            return transcribe_audio_chunk(client, audio_chunk_bytesio, attempt + 1, max_attempts)
        else:
            st.error(f"Failed to transcribe chunk after {max_attempts} attempts.")
            return None


# --- Streamlit App ---
st.set_page_config(page_title="MP3 Transcriber", layout="wide")

st.title("🎤 MP3 Transcriber with Chunking")
st.markdown(f"""
Upload an MP3 file. If it's larger than ~{OPENAI_API_FILE_LIMIT_MB-1}MB, it will be automatically
split into smaller chunks, transcribed, and then reassembled.
This app uses a pre-configured API key.
""")

# --- API Key Handling (Secrets Only - Robust) ---
# (Using the robust version from our previous iteration)
openai_api_key = None
api_key_found = False
error_message_for_user = "Initial check."

openai_section = st.secrets.get("openai")
if openai_section is not None and hasattr(openai_section, "get"):
    potential_key = openai_section.get("api_key")
    if potential_key is not None:
        if isinstance(potential_key, str):
            cleaned_key = potential_key.strip()
            if cleaned_key.startswith("sk-"):
                openai_api_key = cleaned_key
                api_key_found = True
                error_message_for_user = "API key from [openai] section loaded successfully."
            else:
                error_message_for_user = f"The 'api_key' (value: '{cleaned_key}') under '[openai]' in secrets was found but does not start with 'sk-'."
        else:
            error_message_for_user = f"The 'api_key' under '[openai]' in secrets is not a string. Found type: {type(potential_key)}."
    else:
        error_message_for_user = "The '[openai]' section was found in secrets, but the 'api_key' key is missing or has no value within it."
else:
    error_message_for_user = "The '[openai]' section was not found in secrets or is not structured as expected."
    if "OPENAI_API_KEY" in st.secrets: # Fallback for flat key
        error_message_for_user += " Trying flat 'OPENAI_API_KEY'..."
        potential_flat_key = st.secrets.get("OPENAI_API_KEY")
        if potential_flat_key is not None and isinstance(potential_flat_key, str):
            cleaned_flat_key = potential_flat_key.strip()
            if cleaned_flat_key.startswith("sk-"):
                openai_api_key = cleaned_flat_key
                api_key_found = True
                error_message_for_user = "API key loaded successfully from flat 'OPENAI_API_KEY'."
            else:
                error_message_for_user = f"Flat 'OPENAI_API_KEY' (value: '{cleaned_flat_key}') was found but does not start with 'sk-'."
        elif potential_flat_key is not None:
             error_message_for_user = f"Flat 'OPENAI_API_KEY' was found but is not a string. Found type: {type(potential_flat_key)}."
        else:
            error_message_for_user = "Flat 'OPENAI_API_KEY' was found but has no value."

if not api_key_found:
    st.error("OpenAI API Key not found or incorrectly configured in Streamlit Secrets.")
    st.warning(f"""
        **Troubleshooting Detail:** {error_message_for_user}
        Please ensure your OpenAI API Key is configured correctly in your Streamlit Cloud app's Secrets.
    """)
    st.stop()

try:
    client = OpenAI(api_key=openai_api_key)
except Exception as e:
    st.error(f"Failed to initialize OpenAI client: {e}")
    st.stop()

st.divider()

# --- File Uploader ---
uploaded_file = st.file_uploader(
    "Choose an MP3 file",
    type=["mp3"],
    help=f"Upload an MP3 audio file. Max total size handled by chunking. Individual API calls are limited to {OPENAI_API_FILE_LIMIT_MB}MB."
)

if uploaded_file is not None:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.subheader(f"Uploaded Audio ({file_size_mb:.2f} MB)")
    
    # Display audio player (Streamlit might struggle with very large files for the player itself)
    # We read it once for the player, then again if we need to chunk
    try:
        st.audio(uploaded_file, format='audio/mp3')
    except Exception as e:
        st.warning(f"Could not display audio player (file might be too large for direct browser playback): {e}")


    if st.button("Transcribe Audio", type="primary"):
        with st.spinner("Processing audio... Please wait. This may take a while for large files."):
            full_transcription = ""
            uploaded_file.seek(0) # Reset file pointer

            if uploaded_file.size <= OPENAI_API_FILE_LIMIT_BYTES:
                st.info("File is within size limit, transcribing directly...")
                # Pass the file object directly. OpenAI SDK needs a name.
                # The SDK will handle reading it.
                transcription_text = transcribe_audio_chunk(client, uploaded_file)
                if transcription_text:
                    full_transcription = transcription_text
                else:
                    st.error("Direct transcription failed.")
            else:
                st.info(f"File size ({file_size_mb:.2f} MB) exceeds {OPENAI_API_FILE_LIMIT_MB}MB limit. Splitting into chunks...")
                
                try:
                    uploaded_file.seek(0) # Ensure pointer is at the start
                    audio = AudioSegment.from_file(uploaded_file, format="mp3")
                    st.success("Audio loaded for chunking.")
                except Exception as e:
                    st.error(f"Error loading audio file with pydub: {e}")
                    st.error("This might be due to an issue with ffmpeg or the file format. Ensure ffmpeg is in packages.txt and the MP3 is valid.")
                    st.stop()

                # Estimate chunk duration to be under TARGET_CHUNK_SIZE_BYTES
                # This is a rough estimate as bitrate can vary.
                # Duration in ms = (target_bytes * 8 bits/byte) / (bitrate_kbps * 1000 bits/kbps) * 1000 ms/s
                # A simpler way is to just pick a reasonable duration like 10-15 minutes.
                # Let's try chunking by a fixed duration that's likely to be under the size limit.
                # e.g., 10 minutes = 10 * 60 * 1000 ms
                # Or, more dynamically, try to estimate based on file size and duration
                
                # More robust: calculate number of chunks needed
                # For very high bitrate audio, this might still create chunks > 25MB
                # A safer approach might be to target smaller time chunks (e.g., 5-10 mins)
                # and then if an exported chunk is > 25MB, re-chunk that smaller piece.
                # For now, let's use make_chunks with a reasonable time.
                # 10 minutes chunk length
                chunk_length_ms = 10 * 60 * 1000
                audio_chunks = make_chunks(audio, chunk_length_ms)
                num_chunks = len(audio_chunks)

                st.info(f"Splitting into {num_chunks} chunks (approx. {chunk_length_ms/60000:.0f} min each).")
                
                transcriptions_list = []
                chunk_progress = st.progress(0)

                for i, chunk in enumerate(audio_chunks):
                    st.text(f"Processing chunk {i+1} of {num_chunks}...")
                    
                    # Export chunk to an in-memory bytes object
                    chunk_io = io.BytesIO()
                    chunk.export(chunk_io, format="mp3")
                    chunk_io.seek(0) # Reset pointer

                    if chunk_io.getbuffer().nbytes > OPENAI_API_FILE_LIMIT_BYTES:
                        st.error(f"Chunk {i+1} is too large ({chunk_io.getbuffer().nbytes / (1024*1024):.2f}MB) even after splitting by time. "
                                 f"This can happen with very high bitrate audio. Try a smaller file or re-encode.")
                        # Optionally, implement sub-chunking here if desired
                        transcriptions_list.append(f"[ERROR: CHUNK {i+1} TOO LARGE TO PROCESS]")
                        continue # Skip this chunk

                    chunk_transcription = transcribe_audio_chunk(client, chunk_io)
                    if chunk_transcription:
                        transcriptions_list.append(chunk_transcription)
                        st.text(f"Chunk {i+1} transcribed.")
                    else:
                        transcriptions_list.append(f"[ERROR: CHUNK {i+1} FAILED TRANSCRIPTION]")
                        st.warning(f"Transcription for chunk {i+1} failed.")
                    
                    chunk_progress.progress((i + 1) / num_chunks)

                full_transcription = " ".join(filter(None, transcriptions_list))
                chunk_progress.empty() # Remove progress bar

            if full_transcription:
                st.subheader("Transcription Result:")
                st.text_area("Transcription", full_transcription, height=300)
                st.download_button(
                    label="Download Transcription as TXT",
                    data=full_transcription,
                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_transcription.txt",
                    mime="text/plain"
                )
            else:
                st.error("Transcription failed or resulted in empty text. Please check logs if chunking occurred.")
else:
    st.info("Upload an MP3 file to get started.")

st.markdown("---")
st.markdown("Powered by [Streamlit](https://streamlit.io), [OpenAI Whisper](https://openai.com/research/whisper), and [Pydub](https://pydub.com/).")
