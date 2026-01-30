import os

# CHANGED: gpt-4.0-mini -> gpt-4o-mini
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.70"))