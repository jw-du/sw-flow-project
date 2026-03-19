import json

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.core.llm import LLMClient


def main() -> None:
    settings = get_settings()
    print("=== LLM 连通性测试 ===")
    print(json.dumps(
        {
            "provider": settings.llm_provider,
            "base_url": settings.llm_base_url,
            "model": settings.llm_model,
            "api_key_configured": bool(settings.llm_api_key),
        },
        ensure_ascii=False,
        indent=2,
    ))

    resp = LLMClient.chat_completion(
        messages=[
            {"role": "system", "content": "你是一个测试助手。"},
            {"role": "user", "content": "请回复 pong"},
        ],
        temperature=0,
        max_tokens=16,
    )
    content = resp.choices[0].message.content
    print("\n=== 返回内容 ===")
    print(content)


if __name__ == "__main__":
    main()
