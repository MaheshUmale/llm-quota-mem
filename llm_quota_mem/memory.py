import json
import os
import time
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from .config import settings
from .embeddings import Embedder

logger = logging.getLogger(__name__)

class SimpleVectorStore:
    """Distilled lightweight vector store for semantic search."""
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True, parents=True)
        self.index_file = self.storage_path / "index.json"
        self.vectors_file = self.storage_path / "vectors.npy"

        self.metadata: List[Dict[str, Any]] = []
        self.vectors: Optional[np.ndarray] = None
        self._load()

    def _load(self):
        if self.index_file.exists():
            with open(self.index_file, "r") as f:
                self.metadata = json.load(f)
        if self.vectors_file.exists():
            self.vectors = np.load(self.vectors_file)

    def _save(self):
        with open(self.index_file, "w") as f:
            json.dump(self.metadata, f)
        if self.vectors is not None:
            np.save(self.vectors_file, self.vectors)

    def add(self, text: str, vector: List[float], metadata: Dict[str, Any]):
        new_vector = np.array(vector, dtype=np.float32)
        if self.vectors is None:
            self.vectors = new_vector.reshape(1, -1)
        else:
            self.vectors = np.vstack([self.vectors, new_vector])

        metadata["text"] = text
        metadata["timestamp"] = time.time()
        self.metadata.append(metadata)
        self._save()

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if self.vectors is None:
            return []

        query_vec = np.array(query_vector, dtype=np.float32)
        # Cosine similarity
        norms = np.linalg.norm(self.vectors, axis=1)
        q_norm = np.linalg.norm(query_vec)
        if q_norm == 0 or np.any(norms == 0):
            return []

        similarities = np.dot(self.vectors, query_vec) / (norms * q_norm)
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            res = self.metadata[idx].copy()
            res["score"] = float(similarities[idx])
            results.append(res)
        return results

class HybridMemory:
    """Combines semantic long-term memory and structured session state."""
    def __init__(self, user_id: str, project_id: str):
        self.user_id = user_id
        self.project_id = project_id
        storage_dir = Path(settings.MEMORY_DIR) / user_id / project_id
        self.vector_store = SimpleVectorStore(str(storage_dir / "vectors"))
        self.embedder = Embedder()

    async def add_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a new semantic memory."""
        vector = await self.embedder.embed_text(content)
        meta = metadata or {}
        meta["user_id"] = self.user_id
        meta["project_id"] = self.project_id
        self.vector_store.add(content, vector, meta)

    async def recall(self, query: str, top_k: int = 5) -> List[str]:
        """Recall relevant memories based on query string."""
        query_vector = await self.embedder.embed_text(query)
        results = self.vector_store.search(query_vector, top_k=top_k)
        return [res["text"] for res in results if res.get("score", 0) > 0.7]

    async def get_context_summary(self) -> str:
        """Get a summary of the stored memories."""
        if not self.vector_store.metadata:
            return f"Project: {self.project_id}. No memories stored yet."

        # Simple summary: list unique metadata tags and total count
        count = len(self.vector_store.metadata)
        recent = self.vector_store.metadata[-3:]
        recent_texts = [m["text"][:100] + "..." for m in recent]

        summary = (
            f"Project Context: {self.project_id}\n"
            f"Total Memories: {count}\n"
            f"Recent entries:\n- " + "\n- ".join(recent_texts)
        )
        return summary
