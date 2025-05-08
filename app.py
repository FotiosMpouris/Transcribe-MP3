import streamlit as st
from openai import OpenAI
import tempfile # Not strictly needed in this version if transcribe_audio handles file objects well
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

# --- API Key Handling (Secrets Only - More Robust) ---
openai_api_key = None
api_key_found = False
error_message_for_user = "Initial check." # For more detailed feedback

# Try to fetch and validate the nested key first
openai_section = st.secrets.get("openai") # Safely get the [openai] section

if openai_section is not None and hasattr(openai_section, "get"): # Check if section exists and is dict-like
    potential_key = openai_section.get("api_key") # Safely get the api_key from the section

    if potential_key is not None:
        if isinstance(potential_key, str):
            cleaned_key = potential_key.strip() # Remove leading/trailing whitespace
            if cleaned_key.startswith("sk-"):
                openai_api_key = cleaned_key
                api_key_found = True
                error_message_for_user = "API key from [openai] section loaded successfully." # Success
            else:
                error_message_for_user = f"The 'api_key' (value: '{cleaned_key}') under '[openai]' in secrets was found but does not start with 'sk-'."
        else:
            error_message_for_user = f"The 'api_key' under '[openai]' in secrets is not a string. Found type: {type(potential_key)}."
    else:
        # This means [openai] section exists, but 'api_key' is missing within it or is null
        error_message_for_user = "The '[openai]' section was found in secrets, but the 'api_key' key is missing or has no value within it."
else:
    # This means the '[openai]' section itself was not found or wasn't dict-like.
    # As a fallback, we can check for a flat 'OPENAI_API_KEY'
    error_message_for_user = "The '[openai]' section was not found in secrets or is not structured as expected."
    if "OPENAI_API_KEY" in st.secrets:
        error_message_for_user += " Trying flat 'OPENAI_API_KEY'..."
        potential_flat_key = st.secrets.get("OPENAI_API_KEY")
        if potential_flat_key is not None and isinstance(potential_flat_key, str):
            cleaned_flat_key = potential_flat_key.strip()
            if cleaned_flat_key.startswith("sk-"):
                openai_api_key = cleaned_flat_key
                api_key_found = True
                error_message_for_user = "API key loaded successfully from flat 'OPENAI_API_KEY'." # Success
            else:
                error_message_for_user = f"Flat 'OPENAI_API_KEY' (value: '{cleaned_flat_key}') was found but does not start with 'sk-'."
        elif potential_flat_key is not None: # Not a string
             error_message_for_user = f"Flat 'OPENAI_API_KEY' was found but is not a string. Found type: {type(potential_flat_key)}."
        else: # Key OPENAI_API_KEY exists but is null
            error_message_for_user = "Flat 'OPENAI_API_KEY' was found but has no value."


if not api_key_found:
    st.error("OpenAI API Key not found or incorrectly configured in Streamlit Secrets.")
    st.warning(f"""
        **Troubleshooting Detail:** {error_message_for_user}

        Please ensure your OpenAI API Key is configured correctly in your Streamlit Cloud app's Secrets.
        It should be in the format:

        ```toml
        [openai]
        api_key = "YOUR_API_KEY_HERE"
        ```
        (Ensure the key string itself, "YOUR_API_KEY_HERE", doesn't have unexpected leading/trailing spaces unless intended, and starts with "sk-".)

        Current secrets structure detected by the app (or part of it, may not show all nesting if complex):
        ```
        {dict(st.secrets)}
        ```

        **Steps to verify:**
        1. Go to your app settings on Streamlit Community Cloud.
        2. Navigate to the 'Secrets' section.
        3. Carefully check the secret name is `[openai]` and within it, `api_key = "your_actual_key"`.
        4. Ensure your actual key `sk-proj-xxxx` is correctly pasted without extra characters or missing parts.
        5. After saving secrets, Streamlit Cloud should reboot your app. You can also manually reboot it.
    """)
    st.stop()

# Initialize OpenAI client
try:
    client = OpenAI(api_key=openai_api_key)
    # st.success("OpenAI client initialized successfully!") # You can uncomment for a success message
except Exception as e:
    st.error(f"Failed to initialize OpenAI client even after finding API key: {e}")
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
