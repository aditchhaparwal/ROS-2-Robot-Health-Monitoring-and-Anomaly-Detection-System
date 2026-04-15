from pathlib import Path
from typing import Any, Dict

import yaml


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[4] / "config" / "thresholds.yaml"


def load_detector_config(config_path: str = "") -> Dict[str, Any]:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    with path.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)
