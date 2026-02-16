import os

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.o-mini")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.70"))