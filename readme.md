
# Chat with YouTube Videos using Gemini

Streamlit app for chatting with YouTube video content using Google Gemini and RAG.

![Interface Demo](https://via.placeholder.com/800x400.png?text=Streamlit+Chat+Interface)

## 🚀 Features
- ✅ Extracts YouTube video transcript automatically
- 🤖 Summarizes or answers questions using Gemini API
- 🧠 Embedchain + ChromaDB for RAG pipeline
- 🌐 Streamlit Web App Interface
- Session-based chat history


## Requirements
- Python 3.8+
- Google API key ([Get here](https://makersuite.google.com/))

## Quick Start
1. Clone repo:
```bash
git clone https://github.com/mudassir-prg/chat-with-youtube-by-mirza.git
cd chat-with-youtube-gemini
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run app:
```bash
streamlit run app.py
```

## Usage
1. In sidebar:
   - Enter Google API key
   - Paste YouTube URL
   - Click "Load Video"

2. In main window:
   - Chat naturally about video content
   - Conversation history persists per session

## Notes
- First run may take longer to initialize
- Only works with videos that have transcripts
- Temporary database cleared between sessions
```
