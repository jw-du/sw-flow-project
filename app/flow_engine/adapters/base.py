from abc import ABC, abstractmethod
from typing import Any

class SkillAdapter(ABC):
    @abstractmethod
    def execute(self, params: dict[str, Any], context: dict[str, Any]) -> Any:
        pass
