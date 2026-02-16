from llm.schemas import PLANNER_SCHEMA
from prompts.planner import SYSTEM_PROMPT, build_prompt
from core.capabilities import SUPPORTED

def plan_tasks(llm, user_input, df_summary=None):
    result = llm.json(
        SYSTEM_PROMPT,
        build_prompt(user_input, df_summary),
        PLANNER_SCHEMA
    )

    for task in result["tasks"]:
        if task["intent"] not in SUPPORTED:
            task["supported"] = False

    return result
