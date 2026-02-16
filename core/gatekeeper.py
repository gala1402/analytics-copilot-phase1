from llm.schemas import GATEKEEP_SCHEMA
from prompts.gatekeeper import SYSTEM_PROMPT, build_prompt

def gatekeep(llm, user_input, df_summary=None):
    result = llm.json(
        SYSTEM_PROMPT,
        build_prompt(user_input, df_summary),
        GATEKEEP_SCHEMA
    )
    return result
