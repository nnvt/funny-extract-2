import re


class JsonCleaner:
    """Cleans markdown-style fenced JSON blocks into pure JSON string."""

    FENCE_JSON_RE = re.compile(r"```json\s*", re.IGNORECASE)
    FENCE_RE = re.compile(r"```")

    @classmethod
    def clean(cls, text: str) -> str:
        text = cls.FENCE_JSON_RE.sub("", text)
        text = cls.FENCE_RE.sub("", text)
        return text.strip()
