"""Configuration loader."""
import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

ROOT = Path(__file__).parent.parent

def load_env():
    """Load .env file if present."""
    env = ROOT / ".env"
    if env.exists():
        load_dotenv(env)

def load_players(path: str = "config/players.yaml") -> dict:
    """Load players.yaml config."""
    cfg_path = ROOT / path
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def get_port() -> int:
    """Get server port from env (PORT > OPENAGENTS_PORT > 8000)."""
    port_str = os.getenv("PORT") or os.getenv("OPENAGENTS_PORT") or "8000"
    try:
        port = int(port_str)
        return port if 1 <= port <= 65535 else 8000
    except ValueError:
        return 8000

def get_host() -> str:
    return os.getenv("OPENAGENTS_HOST", "0.0.0.0")
