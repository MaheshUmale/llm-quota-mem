import hashlib
import json
from pathlib import Path
from typing import Optional, Any
from .config import settings

class ResponseCache:
    def __init__(self):
        self.cache_dir = Path(settings.CACHE_DIR)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_hash(self, prompt: str, model: str) -> str:
        return hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()

    def get(self, prompt: str, model: str) -> Optional[str]:
        cache_key = self._get_hash(prompt, model)
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file, "r") as f:
                data = json.load(f)
                return data.get("response")
        return None

    def set(self, prompt: str, model: str, response: str):
        cache_key = self._get_hash(prompt, model)
        cache_file = self.cache_dir / f"{cache_key}.json"
        with open(cache_file, "w") as f:
            json.dump({"prompt": prompt, "model": model, "response": response}, f)
