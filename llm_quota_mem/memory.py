import json
import os
import time
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from .config import settings
from .embeddings import Embedder
from .graph import KnowledgeGraph

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

        # Apply time-based decay
        now = time.time()
        decay_factor = 0.1 # Adjust for faster/slower decay

        results = []
        for idx, sim in enumerate(similarities):
            # Ebbinghaus curve approximation: score = similarity * e^(-decay * time_diff)
            time_diff = (now - self.metadata[idx]["timestamp"]) / 3600 # hours
            decayed_score = sim * np.exp(-decay_factor * time_diff)

            res = self.metadata[idx].copy()
            res["score"] = float(decayed_score)
            results.append(res)

        # Sort by decayed score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

class HybridMemory:
    """Combines semantic long-term memory, structured session state, and knowledge graph."""
    def __init__(self, user_id: str, project_id: str):
        self.user_id = user_id
        self.project_id = project_id
        storage_dir = Path(settings.MEMORY_DIR) / user_id / project_id
        self.vector_store = SimpleVectorStore(str(storage_dir / "vectors"))
        self.graph = KnowledgeGraph(str(storage_dir / "graph"))
        self.embedder = Embedder()

    async def add_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a new semantic memory."""
        vector = await self.embedder.embed_text(content)
        meta = metadata or {}
        meta["user_id"] = self.user_id
        meta["project_id"] = self.project_id
        await asyncio.to_thread(self.vector_store.add, content, vector, meta)

    async def recall(self, query: str = None, query_vector: List[float] = None, top_k: int = 5) -> Dict[str, Any]:
        """Recall relevant semantic memories and connected graph entities."""
        if query_vector is None and query:
            query_vector = await self.embedder.embed_text(query)

        if query_vector is None:
            return {"memories": [], "graph": []}

        semantic_results = await asyncio.to_thread(self.vector_store.search, query_vector, top_k=top_k)
        memories = [res["text"] for res in semantic_results if res.get("score", 0) > 0.7]

        # Simple graph lookup if query matches an entity (placeholder logic)
        graph_results = []
        if query:
            words = query.split()
            for word in words:
                if len(word) > 3:
                    rels = self.graph.query(word)
                    if rels:
                        graph_results.append({"entity": word, "relations": rels})

        return {
            "memories": memories,
            "graph": graph_results
        }

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
