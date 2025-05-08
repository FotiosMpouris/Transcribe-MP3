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
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file_object,
            response_format="text"  # You can also use "json", "srt", "vtt"
        )
        return transcript # For "text" response_format, this is the plain text
    except Exception as e:
        st.error(f"Error during transcription: {e}")
        return None

# --- Streamlit App ---
st.set_page_config(page_title="MP3 Transcriber", layout="wide")

st.title("🎤 MP3 Audio Transcriber with OpenAI Whisper")
st.markdown("""
Upload an MP3 file, and this app will transcribe it using OpenAI's Whisper API.
You'll need to provide your OpenAI API key.
""")

# --- Sidebar for API Key Input ---
st.sidebar.header("Configuration")
api_key_input = st.sidebar.text_input(
    "Enter your OpenAI API Key:",
    type="password",
    help="Get your API key from https://platform.openai.com/api-keys"
)

# Check if API key is provided via Streamlit Secrets (preferred for deployment)
# or via user input
openai_api_key = ""
if 'OPENAI_API_KEY' in st.secrets:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    st.sidebar.success("API Key loaded from Secrets!")
elif api_key_input:
    openai_api_key = api_key_input
    st.sidebar.info("API Key entered by user.")
else:
    st.sidebar.warning("Please enter your OpenAI API Key above or set it in Streamlit Secrets.")
    st.warning("Please provide your OpenAI API Key in the sidebar to proceed.")
    st.stop() # Stop execution if no API key

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
    # Display audio player
    st.audio(uploaded_file, format='audio/mp3')

    # --- Transcription Button ---
    if st.button("Transcribe Audio", type="primary"):
        if not openai_api_key:
            st.error("OpenAI API Key is missing. Please enter it in the sidebar.")
        else:
            with st.spinner("Transcribing... Please wait. This may take a few moments."):
                # The uploaded_file is a file-like object, ready to be used
                # For some APIs, you might need to save it to a temporary file first,
                # but OpenAI's client can often handle these directly.
                # Let's pass the file-like object directly.
                # Ensure the file pointer is at the beginning if it was read before.
                uploaded_file.seek(0)
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
                st.error("Transcription failed. Please check the error message above.")
else:
    st.info("Upload an MP3 file to get started.")

st.markdown("---")
st.markdown("Powered by [Streamlit](https://streamlit.io) and [OpenAI Whisper](https://openai.com/research/whisper).")
