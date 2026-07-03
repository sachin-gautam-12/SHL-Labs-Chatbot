# SHL AI Assessment Recommender

Conversational AI system that recommends SHL Individual Assessment Solutions using RAG.

## Project Architecture

- **Backend**: FastAPI (Python 3.12)
- **AI Models**: Google Gemini (`gemini-1.5-flash` for chat, `text-embedding-004` for vectors)
- **Vector DB**: FAISS (In-memory/Disk Cached)
- **Frontend**: HTML5, Vanilla CSS, JS

## Deployment on Render (Free Tier Optimized)

This project has been heavily optimized to deploy successfully on the Render Free Tier (512MB RAM). Local ML models (PyTorch/SentenceTransformers) have been removed, and FAISS indexing is disk-cached to ensure instant startups and avoid memory overflow.

### Deployment Steps
1. Create a new **Web Service** on Render.
2. Connect your GitHub repository.
3. Select **Docker** as the Runtime.
4. Set the Instance Type to **Free** (512MB RAM).

### Required Environment Variables
Add the following in your Render dashboard under "Environment":
- `GEMINI_API_KEY`: Your Google Gemini API Key (Required)
- `LLM_PROVIDER`: `gemini`
- `EMBEDDING_TYPE`: `gemini`
- `RENDER`: `true` (skips slow background scraping during startup)

*Note: PORT is automatically assigned by Render and injected into the Dockerfile.*

## Local Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   Copy `.env.example` to `.env` and insert your API keys.
4. Run the server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Troubleshooting

- **512MB RAM Crash on Render**: Ensure you are not attempting to load PyTorch or local ML models. The `requirements.txt` should strictly use `faiss-cpu` and the Gemini API for embeddings.
- **Empty Recommendations**: Verify your `GEMINI_API_KEY` is valid and has not exhausted its quota.
