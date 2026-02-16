from typing import Optional, Dict, Any, List
from llm.client import LLMClient
from llm.schemas import CLARIFIER_SCHEMA
from prompts.sql import sql_missing_context_questions
from prompts.product import product_missing_context_questions

def clarify_tasks_if_needed(
    llm: LLMClient,
    tasks: List[Dict[str, Any]],
    df_summary: Optional[str] = None
) -> Dict[str, Any]:
    questions: List[str] = []

    for t in tasks:
        if not t["supported"]:
            continue

        intent = t["intent"]
        # Intent-specific minimal clarifications (cheap, deterministic guardrails)
        if intent == "SQL_INVESTIGATION":
            questions += sql_missing_context_questions(t["question"], df_summary=df_summary)
        elif intent == "PRODUCT_ANALYTICS":
            questions += product_missing_context_questions(t["question"])
        elif intent == "PANDAS_TRANSFORM":
            if not df_summary:
                questions.append("You asked for pandas work—please upload a CSV (or describe the dataframe columns).")

    questions = dedupe_preserve_order(questions)
    return {"needs_clarification": len(questions) > 0, "questions": questions}

def dedupe_preserve_order(xs: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in xs:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out
