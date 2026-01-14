import json
from typing import Any, Dict
from openai import OpenAI

from .prompt import AuthorExtractionPrompt
from .utils import JsonCleaner


class LLMClient:
    """Wraps OpenAI-compatible client calls (SambaNova base_url, etc.)."""

    def __init__(self, base_url: str, api_key: str, model_id: str, temperature: float = 0.1):
        self.model_id = model_id
        self.temperature = temperature
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def extract_authors_from_first_page_image(self, base64_png: str) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": AuthorExtractionPrompt.build()},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_png}"},
                        },
                    ],
                }
            ],
            temperature=self.temperature,
        )

        raw_text = response.choices[0].message.content or ""
        cleaned = JsonCleaner.clean(raw_text)
        return json.loads(cleaned)
