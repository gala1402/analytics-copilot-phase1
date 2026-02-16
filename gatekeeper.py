from typing import Optional, Dict, Any
from llm.client import LLMClient
from llm.schemas import GATEKEEP_SCHEMA
from prompts.gatekeeper import GATEKEEP_SYSTEM, gatekeep_user_prompt

def gatekeep(llm: LLMClient, user_input: str, df_summary: Optional[str] = None) -> Dict[str, Any]:
    user = gatekeep_user_prompt(user_input, df_summary=df_summary)
    out = llm.json(GATEKEEP_SYSTEM, user, schema_hint=GATEKEEP_SCHEMA)

    # Basic sanitation/fallbacks
    out.setdefault("questions", [])
    out.setdefault("message", "")
    out.setdefault("reason", "")
    if out.get("decision") not in {"PROCEED", "ASK", "REFUSE"}:
        out["decision"] = "ASK"
        out["message"] = "I need you to rephrase that as an analytics question or request (SQL/pandas/business/product)."
        out["questions"] = ["What outcome are you trying to achieve?", "What dataset/schema should I assume?"]
    return out
