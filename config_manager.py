import json
import os
from pathlib import Path


class ConfigManager:
    """
    Maneja configuración local del usuario.
    - API key
    - idioma objetivo
    """

    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path.cwd()

        self.config_dir = Path(base_dir) / "config"
        self.config_file = self.config_dir / "user_config.json"

        self.config_dir.mkdir(exist_ok=True)

    def exists(self) -> bool:
        return self.config_file.exists()

    def load(self) -> dict:
        if not self.exists():
            return {}

        with open(self.config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: dict):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_api_key(self) -> str | None:
        cfg = self.load()
        return cfg.get("deepseek_api_key")

    def get_target_language(self, default="English") -> str:
        cfg = self.load()
        return cfg.get("target_language", default)
