import hashlib
import logging
import math
import re
from typing import List

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingClient:
    def __init__(self):
        self.embedding_type = settings.EMBEDDING_TYPE.lower()
        self.fallback_mode = False

        if self.embedding_type == "gemini":
            if not settings.GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY is missing. Falling back to local hash embeddings.")
                self.fallback_mode = True
            else:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    # Use the latest supported Gemini embedding model
                    self.model_name = "models/text-embedding-004"
                    logger.info("Gemini Embedding Client Initialized.")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini embedding client: {e}")
                    self.fallback_mode = True
        elif self.embedding_type == "local":
            logger.info("Local ML embeddings have been disabled to prevent memory overflow on Free Tier. Falling back to fast hash embeddings.")
            self.fallback_mode = True
        else:
            raise ValueError(f"Unknown embedding type: {self.embedding_type}")

    def _fallback_embedding(self, text: str) -> List[float]:
        """A deterministic fast hash embedding to be used when offline or out of memory."""
        tokens = re.findall(r"\w+", text.lower())
        # Use 768 dimensions to match Gemini embedding size roughly (Gemini is 768)
        vector = [0.0] * 768
        for token in tokens:
            digest = int(hashlib.sha256(token.encode()).hexdigest()[:8], 16)
            vector[digest % 768] += 1.0

        norm = math.sqrt(sum(v * v for v in vector))
        if norm != 0:
            vector = [v / norm for v in vector]
        return vector

    def embed_query(self, text: str) -> List[float]:
        if not self.fallback_mode:
            try:
                import google.generativeai as genai
                response = genai.embed_content(
                    model=self.model_name,
                    content=text
                )
                return response["embedding"]
            except Exception as e:
                logger.error(f"Gemini API embed_query failed: {e}. Using fallback.")
                
        return self._fallback_embedding(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.fallback_mode:
            try:
                import google.generativeai as genai
                # Batch request if supported, or loop carefully.
                # google.generativeai embed_content supports a list of strings
                response = genai.embed_content(
                    model=self.model_name,
                    content=texts
                )
                
                # if response contains 'embedding' and it's a list of lists:
                if isinstance(response, dict) and "embedding" in response:
                    return response["embedding"]
                elif isinstance(response, list) and len(response) > 0 and "embedding" in response[0]:
                    # Some versions return a list of dicts for batched
                    return [item["embedding"] for item in response]
                else:
                    logger.warning("Unexpected response format from batch embedding. Generating one by one.")
                    
            except Exception as e:
                logger.error(f"Gemini API batch embed_documents failed: {e}. Falling back to single requests.")
                
            # If batching failed or returned unexpectedly, fallback to single requests
            embeddings = []
            import google.generativeai as genai
            for text in texts:
                try:
                    response = genai.embed_content(
                        model=self.model_name,
                        content=text
                    )
                    embeddings.append(response["embedding"])
                except Exception as e:
                    logger.error(f"Failed to embed document via Gemini: {e}")
                    embeddings.append(self._fallback_embedding(text))
            return embeddings

        # Fallback offline path
        return [self._fallback_embedding(t) for t in texts]