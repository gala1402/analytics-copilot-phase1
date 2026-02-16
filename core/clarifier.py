from typing import Optional, Dict, Any, List
from prompts.sql import sql_missing_context_questions


def clarify_tasks_if_needed(
    tasks: List[Dict[str, Any]],
    df_summary: Optional[str] = None
) -> Dict[str, Any]:

    hard_questions: List[str] = []
    soft_questions: List[str] = []

    for task in tasks:

        if not task.get("supported", False):
            continue

        intent = task["intent"]
        question = task["question"]

        # ----------------------------------
        # HARD BLOCKING CASES (STRICT)
        # ----------------------------------
        if intent == "SQL_INVESTIGATION":
            if not df_summary:
                hard_questions.append(
                    "For SQL tasks, please upload a CSV or provide schema/table details."
                )

            hard_questions += sql_missing_context_questions(question, df_summary)

        elif intent == "PANDAS_TRANSFORM":
            if not df_summary:
                hard_questions.append(
                    "For pandas tasks, please upload a CSV or describe the dataframe structure."
                )

        # ----------------------------------
        # EVERYTHING ELSE IS NON-BLOCKING
        # ----------------------------------
        else:
            # Do NOT block business/product questions
            continue

    return {
        "needs_hard_clarification": len(hard_questions) > 0,
        "hard_questions": list(set(hard_questions)),
        "soft_questions": soft_questions  # empty by design
    }
