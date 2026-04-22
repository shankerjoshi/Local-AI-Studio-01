# Local AI Coder Studio

A chatbot built with Streamlit that runs on a local AI model through LM Studio. You can chat with it, upload files, and it shows the model's thinking process if you want.

---

## What it does

- Chat with a locally running AI model
- Upload PDFs, Word docs, text files, or images and ask questions about them
- See the model's internal reasoning while it thinks (optional toggle)
- Saves your chat history across sessions
- Also supports NVIDIA's cloud API if you don't want to run locally

---

## Setup

### What you need installed first

- Python 3.9 or above
- [LM Studio](https://lmstudio.ai/) — this runs the AI model on your computer
- Tesseract OCR (only needed if you want to extract text from images)
  - Windows: [download here](https://github.com/UB-Mannheim/tesseract/wiki)
  - Linux: `sudo apt install tesseract-ocr`
  - Mac: `brew install tesseract`

### Steps

1. Clone or download this repository

2. Install the required Python packages:
```
pip install -r requirements.txt
```

3. Open LM Studio, load a model, and start the local server (it runs on port 1234 by default)

4. Run the app:
```
streamlit run app.py
```

That's it. The app will open in your browser.

---

## Using the NVIDIA cloud API

If you want to use `coding_agent.py` with NVIDIA's API instead of a local model:

1. Get a free API key from [NVIDIA NIM](https://integrate.api.nvidia.com)
2. Copy `.env.example` to a new file called `.env`
3. Paste your key in there
4. Run:
```
python coding_agent.py
```

---

## Folder structure

```
local-ai-coder-studio/
├── app.py
├── utils.py
├── coding_agent.py
├── requirements.txt
├── .env.example
├── .gitignore
└── data/
    └── chat_history.json   (auto-created when you first run the app)
```

---

## Files in this project

| File | What it is |
|------|------------|
| `app.py` | The main chatbot app |
| `utils.py` | Handles reading uploaded files |
| `coding_agent.py` | Standalone script for NVIDIA cloud API |
| `requirements.txt` | Python packages needed |
| `.env.example` | Template for your API keys |

---

## Notes

- The `data/` folder gets created automatically when you first run the app — it stores your chat history
- Don't share your `.env` file, it contains your API key
- If the app says it can't connect to the model, make sure LM Studio's local server is running
