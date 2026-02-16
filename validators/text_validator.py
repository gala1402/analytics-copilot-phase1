def validate_readable_text(text: str) -> str:
    return "\n".join([line.rstrip() for line in text.strip().splitlines()])
