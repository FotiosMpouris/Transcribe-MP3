# MP3 Audio Transcriber

A simple Streamlit application to upload MP3 files and transcribe them using OpenAI's Whisper API.

## Features

-   Upload MP3 files.
-   Transcribe audio using the `whisper-1` model.
-   Display and download the transcription.
-   API key can be provided via user input or (preferably) Streamlit Secrets.

## Deployment to Streamlit Cloud

1.  **Create a GitHub Repository:**
    *   Create a new public or private repository on GitHub.
    *   Add the following files to your repository:
        *   `app.py` (the Streamlit application code)
        *   `requirements.txt` (listing `streamlit` and `openai`)

2.  **Sign up/Log in to Streamlit Community Cloud:**
    *   Go to [share.streamlit.io](https://share.streamlit.io/) and sign up or log in with your GitHub account.

3.  **Deploy the App:**
    *   Click on "New app".
    *   Choose "From existing repo".
    *   Select your GitHub repository.
    *   Select the branch (usually `main` or `master`).
    *   Ensure `app.py` is correctly identified as the main file path.
    *   Click "Deploy!".

4.  **Add OpenAI API Key as a Secret (Highly Recommended):**
    *   Once your app is deployed (or while it's deploying), go to your app's settings in Streamlit Cloud.
    *   Navigate to the "Secrets" section.
    *   Add a new secret:
        *   **Name:** `OPENAI_API_KEY`
        *   **Value:** Your actual OpenAI API key (e.g., `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
    *   Save the secret. The app will automatically restart and use this secret.

    This is more secure than entering the API key directly into the app's UI every time, especially for a publicly accessible app.

## Local Development (Optional)

1.  Clone the repository.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  (Optional) Create a `.env` file in the root directory and add your API key for local testing if you don't want to use Streamlit secrets locally or type it in each time:
    ```
    OPENAI_API_KEY="your_openai_api_key_here"
    ```
    *Note: The provided `app.py` doesn't load from `.env` directly. For local testing without Streamlit Secrets, you'll rely on the text input field in the app's sidebar.*
    *To use `.env` locally, you would typically add `python-dotenv` to `requirements.txt` and `from dotenv import load_dotenv; load_dotenv()` at the top of `app.py`.*

5.  Run the Streamlit app:
    ```bash
    streamlit run app.py
    ```
