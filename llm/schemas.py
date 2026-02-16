GATEKEEP_SCHEMA = """
{
  "decision": "PROCEED|ASK|REFUSE",
  "reason": "string",
  "questions": ["string"]
}
"""

PLANNER_SCHEMA = """
{
  "tasks": [
    {
      "id": "t1",
      "intent": "BUSINESS_STRATEGY|PRODUCT_ANALYTICS|SQL_INVESTIGATION|PANDAS_TRANSFORM|UNSUPPORTED",
      "question": "string",
      "supported": true,
      "requires": ["string"]
    }
  ],
  "confidence": 0.0
}
"""
