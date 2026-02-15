import json
def build_business_prompt(q, s, c):
    schema_str = json.dumps(s) if s else "No Schema"
    return f"""
    Act as a Business Strategist.
    Question: {q}
    Schema: {schema_str}
    
    IF Schema is "No Schema":
      WARN user: "⚠️ No dataset uploaded. Advice is generic."
    ELSE:
      Cite specific columns for every recommendation.
    """