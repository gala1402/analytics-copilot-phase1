import json
def build_product_prompt(q, s, c):
    schema_str = json.dumps(s) if s else "No Schema"
    return f"""
    Act as a Product Analyst.
    Question: {q}
    Schema: {schema_str}
    
    IF specific data (e.g. 'iOS') is missing:
      STATE: "I cannot analyze [Feature] because [Column] is missing."
    """