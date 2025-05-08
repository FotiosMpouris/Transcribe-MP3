import streamlit as st
from openai import OpenAI
import tempfile
import os

# --- Helper Function ---
def transcribe_audio(client, audio_file_object):
    """
    Transcribes an audio file object using OpenAI's Whisper API.
    """
    try:
        audio_file_object.seek(0) # Ensure pointer is at the beginning
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file_object,
            response_format="text"
        )
        return transcript
    except Exception as e:
        st.error(f"Error during transcription: {e}")
        return None

# --- Streamlit App ---
st.set_page_config(page_title="MP3 Transcriber", layout="wide")

st.title("🎤 MP3 Audio Transcriber")
st.markdown("""
Upload an MP3 file, and this app will transcribe it using OpenAI's Whisper API.
This app uses a pre-configured API key.
""")

# --- API Key Handling (Secrets Only - Corrected for TOML structure) ---
openai_api_key = None
api_key_found = False

# Check for the nested structure first
if "openai" in st.secrets and isinstance(st.secrets["openai"], dict) and "api_key" in st.secrets["openai"]:
    openai_api_key = st.secrets["openai"]["api_key"]
    if openai_api_key and isinstance(openai_api_key, str) and openai_api_key.startswith("sk-"):
        api_key_found = True
    else:
        st.error("The 'api_key' found under '[openai]' in secrets is not a valid OpenAI key string.")
        st.stop()
elif "OPENAI_API_KEY" in st.secrets: # Fallback for a flat key, though your format is nested
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    if openai_api_key and isinstance(openai_api_key, str) and openai_api_key.startswith("sk-"):
        api_key_found = True
    else:
        st.error("The 'OPENAI_API_KEY' found in secrets is not a valid OpenAI key string.")
        st.stop()


if not api_key_found:
    st.error("OpenAI API Key not found or incorrectly configured in Streamlit Secrets.")
    st.warning(f"""
        Please ensure your OpenAI API Key is configured in your Streamlit Cloud app's Secrets.
        Based on your description, it should be in the format:

        ```toml
        [openai]
        api_key = "YOUR_API_KEY_HERE"
        ```

        Current secrets structure detected (or part of it):
        ```
        {dict(st.secrets)}
        ```
        (Only top-level keys are shown above if secrets are complex. Ensure the `[openai]` table and `api_key` within it exist.)

        1. Go to your app settings on Streamlit Community Cloud.
        2. Navigate to the 'Secrets' section.
        3. Add/update your secret to match the required structure.
    """)
    st.stop()

# Initialize OpenAI client
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
    help="Upload an MP3 audio file you want to transcribe."
)

if uploaded_file is not None:
    st.subheader("Uploaded Audio")
    st.audio(uploaded_file, format='audio/mp3')

    if st.button("Transcribe Audio", type="primary"):
        with st.spinner("Transcribing... Please wait. This may take a few moments."):
            transcription_text = transcribe_audio(client, uploaded_file)

        if transcription_text:
            st.subheader("Transcription Result:")
            st.text_area("Transcription", transcription_text, height=200)
            st.download_button(
                label="Download Transcription as TXT",
                data=transcription_text,
                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_transcription.txt",
                mime="text/plain"
            )
        else:
            st.error("Transcription failed. Please check for error messages above or ensure the audio is valid.")
else:
    st.info("Upload an MP3 file to get started.")

st.markdown("---")
st.markdown("Powered by [Streamlit](https://streamlit.io) and [OpenAI Whisper](https://openai.com/research/whisper).")
