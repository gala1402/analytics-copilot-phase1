from openai import OpenAI
import json

class LLMClient:
    def __init__(self, config):
        self.client = OpenAI(api_key=config.api_key)
        self.model = config.model
        self.temperature = config.temperature

    def json(self, system, user, schema_hint):
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "system", "content": f"Return strictly valid JSON.\nSchema:\n{schema_hint}"},
                {"role": "user", "content": user}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def text(self, system, user):
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        )
        return response.choices[0].message.content
