import hashlib
import logging
import math
import re
from typing import List, Union
from app.config import settings

logger = logging.getLogger(__name__)

class EmbeddingClient:
    def __init__(self):
        self.embedding_type = settings.EMBEDDING_TYPE.lower()
        self.local_model = None
        self.fallback_mode = False

        if self.embedding_type == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY must be provided for Gemini Embeddings")
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model_name = "models/text-embedding-004"
            logger.info("Initialized Gemini Embeddings client")
        elif self.embedding_type == "local":
            logger.info("Initializing local SentenceTransformers client (this might take a few seconds)...")
            try:
                from sentence_transformers import SentenceTransformer
                self.local_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Initialized local SentenceTransformers (all-MiniLM-L6-v2)")
            except Exception as exc:
                logger.warning("Falling back to lightweight text embeddings because local SentenceTransformers could not be loaded: %s", exc)
                self.fallback_mode = True
        else:
            raise ValueError(f"Unknown embedding type: {self.embedding_type}")

    def _fallback_embedding(self, text: str) -> List[float]:
        tokens = re.findall(r"\w+", text.lower())
        vector = [0.0] * 384
        if not tokens:
            return vector
        for token in tokens:
            digest = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16)
            index = digest % len(vector)
            vector[index] += 1.0
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude:
            vector = [value / magnitude for value in vector]
        return vector

    def embed_query(self, text: str) -> List[float]:
        """Generates embedding vector for a query string."""
        if self.embedding_type == "gemini":
            import google.generativeai as genai
            response = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="RETRIEVAL_QUERY"
            )
            return response["embedding"]
        if self.fallback_mode or self.local_model is None:
            return self._fallback_embedding(text)
        embedding = self.local_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a list of document strings."""
        if self.embedding_type == "gemini":
            import google.generativeai as genai
            embeddings = []
            for text in texts:
                response = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="RETRIEVAL_DOCUMENT"
                )
                embeddings.append(response["embedding"])
            return embeddings
        if self.fallback_mode or self.local_model is None:
            return [self._fallback_embedding(text) for text in texts]
        embeddings = self.local_model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
