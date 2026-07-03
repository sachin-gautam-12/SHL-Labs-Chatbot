import os
import json
import logging
import hashlib
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple, Optional
from app.config import settings
from app.core.embeddings import EmbeddingClient
from app.core.catalog_loader import CatalogLoader

logger = logging.getLogger(__name__)

class AssessmentRetriever:
    def __init__(self):
        self.embeddings_client = EmbeddingClient()
        self.catalog_loader = CatalogLoader()
        self.catalog: List[Dict[str, Any]] = []
        self.index: Optional[faiss.IndexFlatIP] = None
        self.doc_map: Dict[int, Dict[str, Any]] = {}
        
        # Load catalog and initialize FAISS index
        self.initialize_index()

    def _create_document_text(self, item: Dict[str, Any]) -> str:
        """Converts an assessment metadata dict into a rich text block for embedding."""
        skills_str = ", ".join(item.get("skills", []))
        roles_str = ", ".join(item.get("job_roles", []))
        languages_str = ", ".join(item.get("languages", []))
        
        doc_text = (
            f"Assessment Name: {item['name']}\n"
            f"Category: {item['category']}\n"
            f"Test Type: {item['test_type']}\n"
            f"Description: {item['description']}\n"
            f"Skills Measured: {skills_str}\n"
            f"Job Roles targeted: {roles_str}\n"
            f"Languages Supported: {languages_str}\n"
            f"Duration: {item['duration']} minutes\n"
            f"Adaptive Support: {'Yes' if item['adaptive_support'] else 'No'}\n"
            f"Remote Support: {'Yes' if item['remote_support'] else 'No'}\n"
        )
        return doc_text

    def _get_catalog_hash(self) -> str:
        """Generates a hash of the current catalog to detect changes."""
        catalog_str = json.dumps(self.catalog, sort_keys=True)
        return hashlib.md5(catalog_str.encode()).hexdigest()

    def initialize_index(self) -> None:
        """Loads catalog, creates text document formats, and initializes the FAISS database."""
        self.catalog = self.catalog_loader.load_catalog()
        
        if not self.catalog:
            logger.error("Catalog is empty. FAISS index will not be built.")
            return

        # Map indices to assessments
        self.doc_map = {idx: item for idx, item in enumerate(self.catalog)}
        
        # Implement index caching to prevent hitting Gemini API on every startup
        hash_path = os.path.join(settings.DATA_DIR, "catalog_hash.txt")
        current_hash = self._get_catalog_hash()
        
        if os.path.exists(settings.FAISS_INDEX_PATH) and os.path.exists(hash_path):
            try:
                with open(hash_path, "r") as f:
                    saved_hash = f.read().strip()
                if saved_hash == current_hash:
                    logger.info("Catalog unchanged. Loading existing FAISS index from disk...")
                    self.index = faiss.read_index(settings.FAISS_INDEX_PATH)
                    return
                else:
                    logger.info("Catalog changed. Rebuilding FAISS index...")
            except Exception as e:
                logger.warning(f"Error reading FAISS cache. Rebuilding... ({e})")
        else:
            logger.info("FAISS index not found on disk. Building for the first time...")
            
        # Build new index
        texts = [self._create_document_text(item) for item in self.catalog]
        
        logger.info(f"Generating embeddings for {len(texts)} assessments...")
        embeddings = self.embeddings_client.embed_documents(texts)
        
        if not embeddings or len(embeddings) == 0:
            logger.error("Failed to generate embeddings. FAISS index will not be initialized.")
            return
            
        embeddings_np = np.array(embeddings).astype("float32")
        
        dimension = embeddings_np.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product (Cosine Similarity on normalized vectors)
        
        # Normalize vectors for Cosine Similarity
        faiss.normalize_L2(embeddings_np)
        self.index.add(embeddings_np)
        
        # Save FAISS index and hash
        try:
            os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH), exist_ok=True)
            faiss.write_index(self.index, settings.FAISS_INDEX_PATH)
            with open(hash_path, "w") as f:
                f.write(current_hash)
            logger.info(f"Saved FAISS index to {settings.FAISS_INDEX_PATH}")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """Retrieves top_k relevant assessments matching the query string, returning (assessment, score)."""
        if not self.index:
            logger.warning("FAISS index is not initialized. Attempting initialization now...")
            self.initialize_index()
            if not self.index:
                logger.error("FAISS index initialization failed. Cannot retrieve documents.")
                return []

        query_vector = self.embeddings_client.embed_query(query)
        if not query_vector:
            return []
            
        query_np = np.array([query_vector]).astype("float32")
        faiss.normalize_L2(query_np)

        # Search index
        scores, indices = self.index.search(query_np, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            assessment = self.doc_map.get(int(idx))
            if assessment:
                # FAISS IndexFlatIP scores range from -1.0 to 1.0 (Cosine Similarity)
                # Map to confidence 0.0 - 1.0
                confidence = float((score + 1.0) / 2.0)
                results.append((assessment, confidence))
                
        logger.info(f"Retrieved {len(results)} assessments for query: '{query}'")
        return results
