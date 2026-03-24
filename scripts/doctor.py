# 环节自检脚本


import importlib
import json
import sys
from typing import Any

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REQUIRED_IMPORTS = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "pydantic_settings",
    "yaml",
    "openai",
    "httpx",
]


def check_imports() -> dict[str, Any]:
    missing: list[str] = []
    for mod in REQUIRED_IMPORTS:
        try:
            importlib.import_module(mod)
        except Exception:
            missing.append(mod)
    return {"missing_imports": missing, "ok": len(missing) == 0}


def main() -> None:
    from app.core.config import get_settings

    settings = get_settings()
    info = {
        "python": sys.version,
        "settings": {
            "flow_dir": settings.flow_dir,
            "llm_provider": settings.llm_provider,
            "llm_base_url": settings.llm_base_url,
            "llm_model": settings.llm_model,
            "llm_api_key_configured": bool(settings.llm_api_key),
        },
        "imports": check_imports(),
    }
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
