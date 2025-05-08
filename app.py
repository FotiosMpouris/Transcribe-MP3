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
        # Ensure the file pointer is at the beginning if it was read before or passed around.
        audio_file_object.seek(0)
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

# --- API Key Handling (Secrets Only) ---
openai_api_key = None
if 'OPENAI_API_KEY' in st.secrets:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    # st.sidebar.success("OpenAI API Key loaded successfully from Secrets!") # Optional: for debugging if needed
else:
    st.error("OpenAI API Key not found in Streamlit Secrets.")
    st.warning("""
        Please ensure your OpenAI API Key is configured in your Streamlit Cloud app's Secrets.
        1. Go to your app settings on Streamlit Community Cloud.
        2. Navigate to the 'Secrets' section.
        3. Add a secret with the name `OPENAI_API_KEY` and your API key as the value.
    """)
    st.stop() # Stop execution if no API key from secrets

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
