import json
from pydantic import BaseModel, Field

from app.core.llm import LLMClient


class IntentResult(BaseModel):
    query: str
    keywords: list[str] = Field(default_factory=list)
    domain: str = "general"
    task_type: str = "analysis"
    extracted_params: dict[str, str] = Field(default_factory=dict)


class IntentRouter:
    def parse(self, query: str) -> IntentResult:
        prompt = """
        你是一个意图解析器。用户会输入一个任务需求，请提取出任务意图、关键词，并尝试提取输入参数。
        请返回严格的 JSON 格式：
        {
            "domain": "行业研究或政策研究或通用",
            "task_type": "分析或对比或总结",
            "keywords": ["关键词1", "关键词2"],
            "extracted_params": {
                "analysis_topic": "提取出的主题或行业，如房地产、白酒"
            }
        }
        """
        
        try:
            client = LLMClient.get_client()
            if not client:
                return self._fallback_parse(query)
            resp = LLMClient.chat_completion(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query}
                ],
            )
            content = resp.choices[0].message.content
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            parsed = json.loads(content)
            
            return IntentResult(
                query=query.strip(),
                keywords=parsed.get("keywords", []),
                domain=parsed.get("domain", "general"),
                task_type=parsed.get("task_type", "analysis"),
                extracted_params=parsed.get("extracted_params", {})
            )
        except Exception:
            return self._fallback_parse(query)

    def _fallback_parse(self, query: str) -> IntentResult:
        normalized = query.strip()
        lowered = normalized.lower()
        domain = "general"
        topic = ""
        
        for k in ["房地产", "白酒", "银行", "新能源", "半导体"]:
            if k in normalized:
                domain = "industry_research"
                topic = k
                break
                
        if "政策" in normalized or "证监会" in normalized or "央行" in normalized:
            domain = "policy_research"
            
        task_type = "analysis"
        if "对比" in normalized or "比较" in normalized:
            task_type = "comparison"
            
        tokens = [t for t in self._re_split(lowered) if t]
        
        return IntentResult(
            query=normalized, 
            keywords=tokens[:12], 
            domain=domain, 
            task_type=task_type,
            extracted_params={"analysis_topic": topic} if topic else {}
        )

    def _re_split(self, text: str) -> list[str]:
        separators = [",", "，", "。", " ", ";", "；", "\n", "\t"]
        buffer = [text]
        for sep in separators:
            fragments: list[str] = []
            for chunk in buffer:
                fragments.extend(chunk.split(sep))
            buffer = fragments
        return [x.strip() for x in buffer if x.strip()]
