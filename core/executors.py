from typing import Optional, List, Dict, Any
import pandas as pd

from llm.client import LLMClient
from prompts.sql import build_sql_prompt
from prompts.product import build_product_prompt, build_pandas_prompt
from prompts.business import build_business_prompt

from validators.sql_validator import validate_sql
from validators.text_validator import validate_readable_text


def execute_tasks(
    llm: LLMClient,
    tasks: List[Dict[str, Any]],
    df_summary: Optional[str] = None,
    df: Optional[pd.DataFrame] = None,
) -> List[Dict[str, Any]]:

    results: List[Dict[str, Any]] = []

    for task in tasks:

        # Skip unsupported tasks
        if not task.get("supported", False):
            continue

        intent = task.get("intent")
        question = task.get("question")

        try:

            # ----------------------------------------
            # SQL INVESTIGATION
            # ----------------------------------------
            if intent == "SQL_INVESTIGATION":

                prompt = build_sql_prompt(question, df_summary)

                sql_output = llm.text(
                    system="You are a senior analytics engineer. Return only SQL.",
                    user=prompt
                ).strip()

                validated_sql = validate_sql(sql_output, df_summary)

                results.append({
                    "id": task["id"],
                    "intent": intent,
                    "output": f"```sql\n{validated_sql}\n```"
                })

            # ----------------------------------------
            # PRODUCT ANALYTICS
            # ----------------------------------------
            elif intent == "PRODUCT_ANALYTICS":

                prompt = build_product_prompt(question)

                output = llm.text(
                    system="You are a product analytics lead.",
                    user=prompt
                )

                cleaned = validate_readable_text(output)

                results.append({
                    "id": task["id"],
                    "intent": intent,
                    "output": cleaned
                })

            # ----------------------------------------
            # BUSINESS STRATEGY
            # ----------------------------------------
            elif intent == "BUSINESS_STRATEGY":

                prompt = build_business_prompt(question)

                output = llm.text(
                    system="You are a business strategy advisor.",
                    user=prompt
                )

                cleaned = validate_readable_text(output)

                results.append({
                    "id": task["id"],
                    "intent": intent,
                    "output": cleaned
                })

            # ----------------------------------------
            # PANDAS TRANSFORM
            # ----------------------------------------
            elif intent == "PANDAS_TRANSFORM":

                prompt = build_pandas_prompt(question, df_summary)

                output = llm.text(
                    system="You are a Python data engineer. Return only pandas code.",
                    user=prompt
                ).strip()

                results.append({
                    "id": task["id"],
                    "intent": intent,
                    "output": f"```python\n{output}\n```"
                })

            # ----------------------------------------
            # UNKNOWN INTENT SAFETY
            # ----------------------------------------
            else:
                continue

        except Exception as e:
            results.append({
                "id": task.get("id", "unknown"),
                "intent": intent,
                "output": f"Error executing task: {str(e)}"
            })

    return results
