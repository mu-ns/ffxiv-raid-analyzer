import json
import os
from pathlib import Path

APP_DIR_NAME = "ffxiv-raid-analyzer"
CONFIG_FILE = "config.json"
CREDENTIALS_FILE = "credentials.json"


def get_config_dir() -> Path:
    override = os.environ.get("RAID_ANALYZER_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / APP_DIR_NAME


def ensure_config_dir() -> Path:
    d = get_config_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_json(filename: str) -> dict:
    path = ensure_config_dir() / filename
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def write_json(filename: str, data: dict) -> None:
    path = ensure_config_dir() / filename
    path.write_text(json.dumps(data, indent=2))
    path.chmod(0o600)
