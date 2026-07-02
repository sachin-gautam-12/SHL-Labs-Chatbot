SHL AI Assessment Recommender

Version: 1.0
Last Updated: July 2026

A production-ready, conversational AI system that recommends SHL Individual Assessment Solutions using Retrieval-Augmented Generation (RAG), FastAPI, FAISS, and LLM-powered dialogue management.

The system helps recruiters and hiring managers identify the most appropriate SHL assessments through natural conversation while ensuring every recommendation is grounded exclusively in the official SHL assessment catalog.

Overview

Traditional assessment catalogs rely heavily on keyword searches and manual filtering, making it difficult for recruiters who are unsure of the exact assessments they need.

This project solves that challenge by providing an intelligent conversational assistant capable of:

Understanding hiring requirements through natural conversation
Asking clarifying questions before making recommendations
Recommending relevant SHL assessments
Refining recommendations when requirements change
Comparing assessments using catalog evidence
Preventing hallucinations and prompt injection attacks
Returning only official SHL catalog recommendations
Key Features
Conversational AI
Natural language understanding
Multi-turn conversations
Clarification of vague requirements
Context-aware recommendation generation
Conversation refinement
Assessment comparison
Stateless API design
Retrieval-Augmented Generation (RAG)

The recommendation engine uses a complete Retrieval-Augmented Generation pipeline.

SHL Product Catalog
        │
        ▼
Data Processing
        │
        ▼
Chunk Generation
        │
        ▼
Sentence Embeddings
        │
        ▼
FAISS Vector Index
        │
        ▼
Semantic Retrieval
        │
        ▼
Reranking
        │
        ▼
LLM Response Generation
Security

The application includes multiple security layers.

Prompt Injection Detection
System Prompt Protection
Role Injection Prevention
Jailbreak Detection
Off-topic Query Refusal
Catalog-only Recommendations
Safe Response Generation
Project Architecture
Frontend Dashboard
        │
        ▼
FastAPI Backend
        │
 ┌──────┴────────┐
 │               │
Health API    Chat API
 │               │
 └──────┬────────┘
        │
Conversation Engine
        │
 ┌──────┼─────────────────────────────┐
 │      │             │               │
Retriever   Recommender   Comparator   Prompt Guard
        │
        ▼
RAG Pipeline
        │
Embeddings
        │
FAISS Vector Database
        │
SHL Assessment Catalog
Technology Stack
Category	Technology
Language	Python 3.12
Backend	FastAPI
LLM	Gemini 2.5 Flash (Configurable)
Vector Search	FAISS
Embeddings	Sentence Transformers
Prompt Framework	LangChain Core
Web Scraping	BeautifulSoup
Validation	Pydantic
Frontend	HTML5, CSS3, JavaScript
Deployment	Render
Containerization	Docker
API Specification
Health Check
Request
GET /health
Response
{
  "status": "ok"
}
Chat Endpoint
Request
POST /chat
{
  "messages": [
    {
      "role": "user",
      "content": "Hiring a Java Developer"
    }
  ]
}
Response
{
  "reply": "Based on your requirements, here are suitable SHL assessments.",
  "recommendations": [
    {
      "name": "Java 8 (New)",
      "url": "https://www.shl.com/...",
      "test_type": "Knowledge"
    }
  ],
  "end_of_conversation": false
}
Conversation Capabilities

The assistant supports the following behaviors:

Clarification of vague hiring requirements
Context-aware assessment recommendations
Mid-conversation refinement
Assessment comparison
Multi-turn dialogue
Stateless conversation processing
Graceful refusal of unsupported requests
Prompt Injection Protection

The system detects and rejects common prompt injection attacks, including:

Ignore previous instructions
Reveal system prompt
Developer mode requests
Jailbreak attempts
Role override attacks
Prompt extraction requests
Hidden instruction injection

All suspicious requests receive safe refusal responses while maintaining normal conversation flow.

SHL Catalog Processing

The application automatically processes the SHL Individual Test Solutions catalog.

Each assessment stores:

Assessment Name
Description
Official SHL URL
Test Category
Test Type
Skills Measured
Duration
Languages
Remote Availability
Adaptive Testing Support
Recommended Job Roles
Project Structure
shl-ai-recommender/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── utils/
│   ├── config.py
│   └── main.py
│
├── data/
│   ├── shl_catalog.json
│   └── faiss.index
│
├── frontend/
│
├── tests/
│
├── Dockerfile
├── render.yaml
├── requirements.txt
├── README.md
└── report.pdf
Installation

Clone the repository.

git clone https://github.com/sachin-gautam-12/shl-ai-recommender.git
cd shl-ai-recommender

Create a virtual environment.

python -m venv .venv

Activate the environment.

Windows

.venv\Scripts\activate

Linux/macOS

source .venv/bin/activate

Install dependencies.

pip install -r requirements.txt

Create a .env file.

GEMINI_API_KEY=your_api_key
LLM_PROVIDER=gemini
EMBEDDING_MODEL=all-MiniLM-L6-v2

Run the application.

uvicorn app.main:app --reload
Deployment

The project supports deployment on:

Render
Railway
Fly.io
Docker
Hugging Face Spaces

Docker deployment:

docker build -t shl-ai-recommender .
docker run -p 8000:8000 shl-ai-recommender
Testing

Run all automated tests.

pytest tests/

Generate evaluation metrics.

python app/core/evaluator.py

The test suite validates:

API schema
Clarification flow
Recommendation quality
Conversation refinement
Assessment comparison
Prompt injection handling
Invalid requests
Empty requests
Response validation
Evaluation Metrics

The evaluation framework measures:

Recall@10
Precision
Recommendation Accuracy
Groundedness
Hallucination Rate
Latency
Conversation Success Rate
Behavior Probe Success
Compliance Checklist
Requirement	Status
FastAPI Service	✅
GET /health	✅
POST /chat	✅
Stateless API	✅
Clarification Questions	✅
Assessment Recommendations	✅
Recommendation Refinement	✅
Assessment Comparison	✅
Prompt Injection Protection	✅
Catalog-only Responses	✅
RAG Implementation	✅
FAISS Vector Search	✅
Evaluation Framework	✅
Docker Support	✅
Render Deployment	✅
Future Improvements
Automatic catalog synchronization
Hybrid search (semantic + keyword)
Cross-encoder reranking
Redis response caching
Streaming responses
Enhanced analytics dashboard
Multi-language support
Developer

Sachin Kumar Singh

B.Tech – Computer Science & Engineering

Email: sk7505875@gmail.com

GitHub: https://github.com/sachin-gautam-12

LinkedIn: https://www.linkedin.com/in/sachin-kumar-singh-5a193522a/

License

This project is licensed under the MIT License.
