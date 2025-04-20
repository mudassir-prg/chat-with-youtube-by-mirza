import tempfile
import streamlit as st
from embedchain import App
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Tuple
import google.generativeai as genai

# It's good practice to define the embedding model explicitly
GOOGLE_EMBEDDING_MODEL = "models/embedding-001" # Or other suitable embedding model

def embedchain_bot(db_path: str, api_key: str) -> App:
    """Initializes and returns an embedchain App instance."""
    # Note: api_key is passed to the llm config directly,
    # but NOT needed in the embedder config because genai.configure handles it globally.
    return App.from_config(
        config={
            "llm": {
                "provider": "google",
                "config": {
                    "model": "models/gemini-1.5-pro-latest",
                    "temperature": 0.5,
                    "api_key": api_key, # LLM config often takes the key directly
                    "top_p": 0.95, # Example: Add other relevant LLM params if needed
                }
            },
            "vectordb": {
                "provider": "chroma",
                "config": {
                    "dir": db_path
                }
            },
            "embedder": {
                "provider": "google",
                "config": {
                    # REMOVED 'api_key': api_key FROM HERE
                    "model": GOOGLE_EMBEDDING_MODEL # Specify the embedding model
                }
            },
        }
    )

def extract_video_id(video_url: str) -> str:
    """Extracts the video ID from various YouTube URL formats."""
    if "youtube.com/watch?v=" in video_url:
        return video_url.split("v=")[-1].split("&")[0]
    elif "youtube.com/shorts/" in video_url:
        # Handle potential query parameters after shorts ID
        return video_url.split("/shorts/")[-1].split("?")[0].split("&")[0]
    elif "youtu.be/" in video_url:
        # Handle short URLs like youtu.be/VIDEO_ID
        return video_url.split("youtu.be/")[-1].split("?")[0].split("&")[0]
    else:
        # You might want to add more robust URL parsing or validation
        st.warning("Could not parse YouTube URL format reliably. Attempting extraction...")
        # Fallback attempt (less reliable)
        parts = video_url.split("/")
        if len(parts) > 1:
            potential_id = parts[-1].split("?")[0].split("&")[0]
            if len(potential_id) == 11: # Standard YouTube ID length
                 return potential_id
        raise ValueError("Invalid or unrecognized YouTube URL format.")


def fetch_video_data(video_url: str) -> Tuple[str, str]:
    """Fetches video transcript. Returns ('Unknown', transcript) or ('Unknown', error_message)."""
    try:
        video_id = extract_video_id(video_url)
        # Fetch available transcripts and prefer English if possible
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            # Try fetching the manually created or generated English transcript
            transcript = transcript_list.find_generated_transcript(['en']).fetch()
        except Exception:
             # If English fails, try finding any available transcript
             st.warning("English transcript not found, fetching first available language.")
             transcript = transcript_list.find_transcript(transcript_list.manually_created_transcripts.keys() | transcript_list.generated_transcripts.keys()).fetch()

        transcript_text = " ".join([entry["text"] for entry in transcript])
        # Placeholder for title - ideally fetch using pytube or similar if needed
        title = f"Video (ID: {video_id})"
        return title, transcript_text
    except Exception as e:
        st.error(f"Error fetching transcript for {video_url}: {e}")
        return "Unknown", "No transcript available for this video."

# --- Streamlit App ---
st.set_page_config(layout="wide") # Optional: Use wider layout

st.title("Chat with YouTube Video using Gemini 🤖")
st.caption("Powered by Google's Gemini API & Embedchain")

# Use session state to store app instance and avoid re-initialization on every interaction
if 'app' not in st.session_state:
    st.session_state.app = None
if 'db_path' not in st.session_state:
    st.session_state.db_path = None
if 'current_video_url' not in st.session_state:
    st.session_state.current_video_url = ""
if "messages" not in st.session_state:
    st.session_state.messages = []


# Sidebar for API key and video input
with st.sidebar:
    st.header("Configuration")
    google_api_key = st.text_input("Google API Key", type="password", key="api_key_input")

    if google_api_key:
        try:
            genai.configure(api_key=google_api_key)
            # Test the key with a simple listing model to ensure it's valid
            # list(genai.list_models()) # Uncomment to test key validity immediately
            st.success("Google API Key configured!", icon="✅")

            # Initialize app only once or if the key changes
            if st.session_state.app is None:
                 with st.spinner("Initializing Embedchain App..."):
                    st.session_state.db_path = tempfile.mkdtemp()
                    st.session_state.app = embedchain_bot(st.session_state.db_path, google_api_key)
                 st.info("App initialized.")

        except Exception as e:
            st.error(f"Failed to configure Google API: {e}", icon="🚨")
            st.session_state.app = None # Reset app if config fails
            google_api_key = None # Ensure key is considered invalid

    st.header("Video Input")
    video_url_input = st.text_input("Enter YouTube Video URL", key="video_url_input")

    if st.button("Load Video", key="load_video_button", disabled=not google_api_key or not video_url_input):
        if st.session_state.app and video_url_input and video_url_input != st.session_state.current_video_url:
            with st.spinner(f"Fetching transcript for {video_url_input}..."):
                try:
                    title, transcript = fetch_video_data(video_url_input)
                    if transcript != "No transcript available for this video.":
                        # Clear previous video data if any? Or allow multiple?
                        # For simplicity, let's assume we replace the context for now.
                        # You might need to manage multiple sources if needed.
                        # st.session_state.app.reset() # Uncomment to clear previous context

                        st.session_state.app.add(transcript, data_type="text", metadata={"title": title, "url": video_url_input})
                        st.session_state.current_video_url = video_url_input
                        st.session_state.messages = [] # Reset chat history for new video
                        st.success(f"Added video '{title}' to knowledge base!", icon="🎬")
                    else:
                        st.warning(f"No transcript found for video '{title}'. Cannot add to knowledge base.", icon="⚠️")
                except ValueError as e:
                    st.error(f"Invalid YouTube URL: {e}", icon="🚫")
                except Exception as e:
                    st.error(f"Error processing video: {e}", icon="🚨")
        elif not st.session_state.app:
            st.warning("Please enter a valid API key first.")
        elif video_url_input == st.session_state.current_video_url:
             st.info("This video is already loaded.")


# Main Chat Interface
st.header("Chat Interface")

if not st.session_state.current_video_url:
     st.info("Please enter a YouTube URL and click 'Load Video' in the sidebar.")
elif not st.session_state.app:
     st.warning("App not initialized. Please check API key.")
else:
    st.info(f"Currently chatting with: {st.session_state.current_video_url}")

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask something about the video..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            with st.spinner("Analyzing with Gemini..."):
                try:
                    response = st.session_state.app.chat(prompt)
                    # Handle potential response object vs string
                    answer = response if isinstance(response, str) else getattr(response, 'response', str(response))

                    # Simulate stream of response with milliseconds delay (if response is long)
                    # For actual streaming, you'd need to use app.stream() if available
                    # or handle chunks from the LLM directly.
                    # For simplicity, just display the full response here.
                    full_response = answer
                    message_placeholder.markdown(full_response)

                except Exception as e:
                    full_response = f"Sorry, an error occurred: {str(e)}"
                    message_placeholder.error(full_response)

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

# Cleanup temporary directory (optional, but good practice if running locally long-term)
# Note: Streamlit's execution model might make explicit cleanup tricky without server lifecycle hooks.
# The OS usually handles temp dir cleanup eventually.
# import atexit
# import shutil
# if st.session_state.db_path:
#     atexit.register(shutil.rmtree, st.session_state.db_path, ignore_errors=True)