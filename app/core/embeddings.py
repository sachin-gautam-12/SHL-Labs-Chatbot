import hashlib
import logging
import math
import re
from typing import List

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingClient:
    def __init__(self):
        self.embedding_type = settings.EMBEDDING_TYPE.lower()
        self.local_model = None
        self.fallback_mode = False

        if self.embedding_type == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY must be provided")

            genai.configure(api_key=settings.GEMINI_API_KEY)

            # Compatible model
            self.model_name = "models/embedding-001"

            logger.info("Gemini Embedding Client Initialized")

        elif self.embedding_type == "local":
            try:
                from sentence_transformers import SentenceTransformer

                self.local_model = SentenceTransformer(
                    "all-MiniLM-L6-v2"
                )

                logger.info("Local embedding model loaded.")

            except Exception as e:
                logger.warning(
                    "Falling back to hash embeddings: %s", e
                )
                self.fallback_mode = True

        else:
            raise ValueError("Unknown embedding type")

    def _fallback_embedding(self, text: str) -> List[float]:
        tokens = re.findall(r"\w+", text.lower())

        vector = [0.0] * 384

        for token in tokens:
            digest = int(
                hashlib.sha256(token.encode()).hexdigest()[:8],
                16,
            )

            vector[digest % 384] += 1.0

        norm = math.sqrt(sum(v * v for v in vector))

        if norm != 0:
            vector = [v / norm for v in vector]

        return vector

    def embed_query(self, text: str) -> List[float]:

        if self.embedding_type == "gemini":

            response = genai.embed_content(
                model=self.model_name,
                content=text
            )

            return response["embedding"]

        if self.fallback_mode:
            return self._fallback_embedding(text)

        return self.local_model.encode(
            text,
            convert_to_numpy=True
        ).tolist()

    def embed_documents(
        self,
        texts: List[str]
    ) -> List[List[float]]:

        if self.embedding_type == "gemini":

            embeddings = []

            for text in texts:

                response = genai.embed_content(
                    model=self.model_name,
                    content=text
                )

                embeddings.append(
                    response["embedding"]
                )

            return embeddings

        if self.fallback_mode:
            return [
                self._fallback_embedding(t)
                for t in texts
            ]

        return self.local_model.encode(
            texts,
            convert_to_numpy=True
        ).tolist()