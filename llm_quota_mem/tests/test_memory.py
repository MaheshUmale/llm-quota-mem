import pytest
import numpy as np
from llm_quota_mem.memory import SimpleVectorStore

def test_vector_store(tmp_path):
    storage_dir = tmp_path / "vectors"
    store = SimpleVectorStore(str(storage_dir))

    vec1 = [0.1, 0.2, 0.3]
    store.add("Hello World", vec1, {"meta": "data"})

    # Reload store
    store2 = SimpleVectorStore(str(storage_dir))
    assert len(store2.metadata) == 1
    assert store2.metadata[0]["text"] == "Hello World"

    # Search
    results = store2.search([0.1, 0.21, 0.3], top_k=1)
    assert len(results) == 1
    assert results[0]["text"] == "Hello World"
    assert results[0]["score"] > 0.99
