from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class AuthorRecord:
    filename: str
    name: str
    role: str
    is_corresponding: Optional[bool] = None
    affiliation: Optional[str] = None
    email: Optional[str] = None

    @staticmethod
    def from_llm_dict(d: Dict[str, Any], filename: str) -> "AuthorRecord":
        return AuthorRecord(
            filename=filename,
            name=d.get("name", ""),
            role=d.get("role", ""),
            is_corresponding=d.get("is_corresponding", None),
            affiliation=d.get("affiliation", None),
            email=d.get("email", None),
        )
