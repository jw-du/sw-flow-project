from openai import OpenAI

from app.core.config import get_settings


class LLMClient:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            settings = get_settings()
            api_key = (settings.llm_api_key or "").strip()
            if api_key.startswith("'") and api_key.endswith("'") and len(api_key) >= 2:
                api_key = api_key[1:-1].strip()
            if api_key.startswith('"') and api_key.endswith('"') and len(api_key) >= 2:
                api_key = api_key[1:-1].strip()
            if not api_key:
                return None
            cls._client = OpenAI(
                api_key=api_key,
                base_url=settings.llm_base_url,
            )
        return cls._client

    @classmethod
    def chat_completion(cls, messages: list[dict], model: str = None, **kwargs):
        client = cls.get_client()
        if not client:
            raise ValueError("LLM_API_KEY 未配置，请在 .env 中设置")

        settings = get_settings()
        model_id = model or settings.llm_model

        if not model_id:
            raise ValueError("LLM_MODEL 未配置，请在 .env 中设置")

        return client.chat.completions.create(
            model=model_id,
            messages=messages,
            **kwargs
        )
