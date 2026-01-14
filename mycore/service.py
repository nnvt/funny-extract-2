from typing import List

from .models import AuthorRecord


class AuthorExtractorService:
    """Coordinates PDF rendering + LLM extraction + flattening into AuthorRecord."""

    def __init__(self, renderer, llm):
        self.renderer = renderer
        self.llm = llm

    def extract_from_pdf(self, pdf_path: str, filename: str) -> List[AuthorRecord]:
        try:
            img_b64 = self.renderer.first_page_to_base64_png(pdf_path)
            data = self.llm.extract_authors_from_first_page_image(img_b64)

            authors = data.get("authors", [])
            return [AuthorRecord.from_llm_dict(a, filename) for a in authors]

        except Exception as e:
            # Keep your original behavior: return an error row for that file
            return [AuthorRecord(filename=filename, name="ERROR", role=str(e))]
