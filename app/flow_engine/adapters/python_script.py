import json
import subprocess
from pathlib import Path
from typing import Any

from app.flow_engine.adapters.base import SkillAdapter
from app.core.config import get_settings

class PythonScriptAdapter(SkillAdapter):
    def __init__(self, skill_name: str):
        self.skill_name = skill_name
        self.settings = get_settings()
        self.skill_dir = Path("skills") / skill_name
        
    def execute(self, params: dict[str, Any], context: dict[str, Any]) -> Any:
        script_path = self.find_script()
        if not script_path:
            raise FileNotFoundError(f"No executable script found for skill {self.skill_name}")

        cmd = ["python", str(script_path)]
        
        positional = params.pop("_positional", [])
        if isinstance(positional, list):
            cmd.extend([str(p) for p in positional])
            
        for k, v in params.items():
            if k.startswith("_"): continue # skip internal keys
            
            flag = f"--{k.replace('_', '-')}"
            
            if isinstance(v, bool):
                if v:
                    cmd.append(flag)
            else:
                cmd.append(flag)
                cmd.append(str(v))

        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding="utf-8",
                check=True
            )
            stdout = result.stdout.strip()
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                return {"text": stdout, "raw": True}
                
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Script execution failed: {e.stderr}")

    def find_script(self) -> Path | None:
        candidates = ["scripts/search.py", "scripts/main.py", f"scripts/{self.skill_name}.py", "main.py", f"{self.skill_name}.py"]
        for c in candidates:
            p = self.skill_dir / c
            if p.exists():
                return p
        return None
