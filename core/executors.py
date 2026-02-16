from prompts.sql import build_sql_prompt
from prompts.product import build_product_prompt
from prompts.business import build_business_prompt
from validators.sql_validator import validate_sql
from validators.text_validator import clean_text

def execute_tasks(llm, tasks, df_summary=None):

    results = []

    for t in tasks:
        if not t["supported"]:
            continue

        if t["intent"] == "SQL_INVESTIGATION":
            prompt = build_sql_prompt(t["question"], df_summary)
            sql = llm.text("Return SQL only.", prompt)
            sql = validate_sql(sql, df_summary)
            results.append({"id": t["id"], "output": f"```sql\n{sql}\n```"})

        elif t["intent"] == "PRODUCT_ANALYTICS":
            out = llm.text("Answer as product analytics lead.", build_product_prompt(t["question"]))
            results.append({"id": t["id"], "output": clean_text(out)})

        elif t["intent"] == "BUSINESS_STRATEGY":
            out = llm.text("Answer as business strategist.", build_business_prompt(t["question"]))
            results.append({"id": t["id"], "output": clean_text(out)})

    return results
