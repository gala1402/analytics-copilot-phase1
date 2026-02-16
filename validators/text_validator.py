def validate_readable_text(text: str) -> str:
    # Minimal guardrail: trim excessive whitespace
    return "\n".join([line.rstrip() for line in text.strip().splitlines()])
