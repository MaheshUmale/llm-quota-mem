import pytest
from llm_quota_mem.graph import KnowledgeGraph

def test_knowledge_graph(tmp_path):
    storage_dir = tmp_path / "graph"
    graph = KnowledgeGraph(str(storage_dir))

    graph.add_relation("ERP", "is-a", "Monolith")
    graph.add_relation("Cloud", "hosts", "Microservices")
    graph.add_relation("ERP", "migrates-to", "Cloud")

    # Query
    rels = graph.query("ERP")
    assert len(rels) == 2

    # Connected
    connected = graph.get_connected_entities("ERP", depth=2)
    assert "monolith" in connected
    assert "cloud" in connected
    assert "microservices" in connected
