import json
import subprocess
from datetime import datetime, timedelta
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

        local_params = dict(params or {})
        positional = local_params.pop("_positional", [])
        if (not isinstance(positional, list) or len(positional) == 0) and "start_date" in local_params and "end_date" in local_params:
            raw_start = local_params.get("start_date")
            raw_end = local_params.get("end_date")
            if raw_start not in (None, "") and raw_end not in (None, ""):
                positional = [local_params.pop("start_date"), local_params.pop("end_date")]
        if (not isinstance(positional, list) or len(positional) == 0) and self.skill_name == "eastmoney-calendar":
            positional = self._build_calendar_positional(local_params, context)

        if isinstance(positional, list):
            cmd.extend([str(p) if p is not None else "" for p in positional])
            
        for k, v in local_params.items():
            if k.startswith("_"): continue # skip internal keys
            
            flag = f"--{k.replace('_', '-')}"
            if k in {"output_path", "output_file"}:
                flag = "--output"
            
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
                errors="replace",
                check=True
            )
            stdout = (result.stdout or "").strip()
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                return {"text": stdout, "raw": True}
                
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Script execution failed: {(e.stderr or '').strip()}")

    def find_script(self) -> Path | None:
        candidates = [
            "scripts/search.py",
            "scripts/main.py",
            "scripts/generate_report.py",
            f"scripts/{self.skill_name}.py",
            "main.py",
            f"{self.skill_name}.py",
        ]
        for c in candidates:
            p = self.skill_dir / c
            if p.exists():
                return p
        scripts_dir = self.skill_dir / "scripts"
        if scripts_dir.exists() and scripts_dir.is_dir():
            py_files = sorted([p for p in scripts_dir.glob("*.py") if p.is_file()])
            if py_files:
                return py_files[0]
        return None

    def _build_calendar_positional(self, local_params: dict[str, Any], context: dict[str, Any]) -> list[str]:
        alias_start = ["start_date", "from_date", "begin_date", "date_start", "calendar_start_date"]
        alias_end = ["end_date", "to_date", "finish_date", "date_end", "calendar_end_date"]

        start = None
        end = None
        for key in alias_start:
            if key in local_params:
                start = local_params.pop(key)
                break
        for key in alias_end:
            if key in local_params:
                end = local_params.pop(key)
                break

        start = (str(start).strip() if start is not None else "")
        end = (str(end).strip() if end is not None else "")

        if not start:
            start = datetime.now().strftime("%Y-%m-%d")
        if not end:
            inputs = context.get("inputs", {}) if isinstance(context, dict) else {}
            try:
                days = int(inputs.get("forward_days", 7))
            except Exception:
                days = 7
            end = (datetime.now() + timedelta(days=max(days, 1))).strftime("%Y-%m-%d")

        return [start[:10], end[:10]]
