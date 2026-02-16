from typing import Optional, Dict, Any
from llm.client import LLMClient
from llm.schemas import ROUTER_SCHEMA
from prompts.router import ROUTER_SYSTEM, router_user_prompt

def route_intents(llm: LLMClient, user_input: str, df_summary: Optional[str] = None) -> Dict[str, Any]:
    user = router_user_prompt(user_input, df_summary=df_summary)
    out = llm.json(ROUTER_SYSTEM, user, schema_hint=ROUTER_SCHEMA)
    out.setdefault("intents", [])
    out.setdefault("has_multiple_intents", len(out["intents"]) > 1)
    return out
