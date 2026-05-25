import json
from pathlib import Path
from typing import List, Dict, Any, Set
import logging

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """Lightweight triple-store for EA relationship mapping."""
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True, parents=True)
        self.graph_file = self.storage_path / "graph.json"
        # triples: List of [subject, predicate, object]
        self.triples: List[List[str]] = []
        self._load()

    def _load(self):
        if self.graph_file.exists():
            with open(self.graph_file, "r") as f:
                self.triples = json.load(f)

    def _save(self):
        with open(self.graph_file, "w") as f:
            json.dump(self.triples, f)

    def add_relation(self, subject: str, predicate: str, obj: str):
        triple = [subject.lower(), predicate.lower(), obj.lower()]
        if triple not in self.triples:
            self.triples.append(triple)
            self._save()

    def query(self, entity: str) -> List[Dict[str, str]]:
        entity = entity.lower()
        results = []
        for s, p, o in self.triples:
            if s == entity:
                results.append({"relation": p, "target": o, "type": "outbound"})
            elif o == entity:
                results.append({"relation": p, "target": s, "type": "inbound"})
        return results

    def get_connected_entities(self, entity: str, depth: int = 1) -> Set[str]:
        entity = entity.lower()
        connected = {entity}
        for _ in range(depth):
            new_entities = set()
            for s, p, o in self.triples:
                if s in connected:
                    new_entities.add(o)
                if o in connected:
                    new_entities.add(s)
            connected.update(new_entities)
        connected.remove(entity)
        return connected
