# ... imports ...

def get_confidence(client: OpenAI, output: str) -> dict:
    resp = client.chat.completions.create(
        # CHANGED: gpt-4.0-mini -> gpt-4o-mini
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": CONF_SYSTEM},
            {"role": "user", "content": output[:7000]},
        ],
        temperature=0,
    )
    # ... rest of function ...