from llm.schemas import GATEKEEP_SCHEMA
from prompts.gatekeeper import SYSTEM_PROMPT, build_prompt

def gatekeep(llm, user_input, df_summary=None):
    result = llm.json(
        SYSTEM_PROMPT,
        build_prompt(user_input, df_summary),
        GATEKEEP_SCHEMA
    )

    # ---- Hardening / fallback rules ----
    # If model returns ASK but blocking is false/missing, treat as PROCEED.
    blocking = bool(result.get("blocking", False))
    decision = result.get("decision", "PROCEED")

    if decision == "ASK" and not blocking:
        result["decision"] = "PROCEED"

    # Ensure keys exist
    result.setdefault("questions", [])
    result.setdefault("message", "")
    result.setdefault("reason", "")
    result.setdefault("blocking", blocking)

    return result
