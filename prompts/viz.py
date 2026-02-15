def build_viz_prompt(question, schema, df_head):
    return f"""
You are a Python Data Visualization Expert. 
Dataset Schema: {schema}
First 3 rows: {df_head}

Task: Generate Python code using Plotly to answer: {question}

Requirements:
1. Assume the dataframe is already loaded as `df`.
2. Use Plotly Express (`px`).
3. Set the chart title and labels clearly.
4. Output ONLY the Python code block wrapped in triple backticks.
5. Do not explain the code.
""".strip()