from typing import Optional, Dict, Any, List
from prompts.sql import sql_missing_context_questions

def clarify_tasks_if_needed(
    tasks: List[Dict[str, Any]],
    df_summary: Optional[str] = None
) -> Dict[str, Any]:

    hard_questions: List[str] = []

    for task in tasks:
        if not task.get("supported", False):
            continue

        intent = task["intent"]
        question = task["question"]

        if intent == "SQL_INVESTIGATION":
            if not df_summary:
                hard_questions.append("For SQL tasks, please upload a CSV or provide schema/table details.")
            hard_questions += sql_missing_context_questions(question, df_summary)

        elif intent == "PANDAS_TRANSFORM":
            if not df_summary:
                hard_questions.append("For pandas tasks, please upload a CSV or describe the dataframe structure.")

        # Everything else never blocks
        else:
            continue

    # de-dupe while preserving order
    seen = set()
    deduped = []
    for q in hard_questions:
        if q not in seen:
            deduped.append(q)
            seen.add(q)

    return {
        "needs_hard_clarification": len(deduped) > 0,
        "hard_questions": deduped,
        "soft_questions": []
    }
