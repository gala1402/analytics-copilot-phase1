import os
from dataclasses import dataclass

@dataclass
class AppConfig:
    provider: str
    api_key: str
    model: str
    temperature: float

    @staticmethod
    def from_env():
        return AppConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("TEMPERATURE", "0.1"))
        )
