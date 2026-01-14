import streamlit as st
import fitz  # PyMuPDF
import base64
import json
import re
import pandas as pd
import os
import time
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

from openai import OpenAI
from dotenv import load_dotenv


# =========================
# Domain model
# =========================
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


# =========================
# Utilities
# =========================
class JsonCleaner:
    """Cleans markdown-style fenced JSON blocks into pure JSON string."""

    FENCE_JSON_RE = re.compile(r"```json\s*", re.IGNORECASE)
    FENCE_RE = re.compile(r"```")

    @classmethod
    def clean(cls, text: str) -> str:
        text = cls.FENCE_JSON_RE.sub("", text)
        text = cls.FENCE_RE.sub("", text)
        return text.strip()


class PdfRenderer:
    """Renders a PDF page to base64 PNG."""

    def __init__(self, zoom: float = 2.0):
        self.zoom = zoom

    def first_page_to_base64_png(self, pdf_path: str) -> str:
        doc = fitz.open(pdf_path)
        try:
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom, self.zoom))
            img_data = pix.tobytes("png")
            return base64.b64encode(img_data).decode("utf-8")
        finally:
            doc.close()


# =========================
# LLM client wrapper
# =========================
class AuthorExtractionPrompt:
    @staticmethod
    def build() -> str:
        return """
Analyze this image of a research paper's first page.
Extract the author list and determine their specific roles based on these RULES:

1. **First Author**: The first name listed is ALWAYS the "First Author", UNLESS a symbol indicates equal contribution.
2. **Co-First Authors**: If a symbol (like † or ‡) notes "These authors contributed equally", then label ALL marked authors as "Co-First Author".
3. **Corresponding Author**: Look for an asterisk (*) or an email address in the footnotes. This person is "Corresponding Author" (they can also be First or Co-Author).
4. **Co-Author**: Everyone else is a "Co-Author".

Return ONLY a valid JSON object:
{
  "authors": [
    {
      "name": "Name",
      "role": "First Author / Co-First Author / Co-Author",
      "is_corresponding": true/false,
      "affiliation": "Affiliation",
      "email": "Email (only if available)"
    }
  ]
}
""".strip()


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


# =========================
# Application service
# =========================
class AuthorExtractorService:
    """Coordinates PDF rendering + LLM extraction + flattening into AuthorRecord."""

    def __init__(self, renderer: PdfRenderer, llm: LLMClient):
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


# =========================
# Persistence / temp file helper
# =========================
class TempPdfWriter:
    """Writes an uploaded file to a stable temp path (single-file reuse)."""

    def __init__(self, temp_path: str = "temp_paper.pdf"):
        self.temp_path = temp_path

    def write(self, uploaded_file) -> str:
        with open(self.temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return self.temp_path


# =========================
# Streamlit UI
# =========================
class StreamlitAuthorApp:
    def __init__(self, extractor: AuthorExtractorService, temp_writer: TempPdfWriter):
        self.extractor = extractor
        self.temp_writer = temp_writer

    def run(self):
        st.set_page_config(layout="wide")
        st.title("UET funny lab AI")
        st.markdown("Output la csv nhe mn")

        uploaded_files = st.file_uploader(
            "Choose PDF files", type="pdf", accept_multiple_files=True
        )

        if not uploaded_files:
            return

        if st.button(f"Process {len(uploaded_files)} Files"):
            all_records: List[AuthorRecord] = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, uf in enumerate(uploaded_files):
                status_text.write(f"Processing: {uf.name} ({i+1}/{len(uploaded_files)})")

                pdf_path = self.temp_writer.write(uf)
                records = self.extractor.extract_from_pdf(pdf_path, uf.name)
                all_records.extend(records)

                progress_bar.progress((i + 1) / len(uploaded_files))
                time.sleep(0.5)

            st.success("Processing Complete!")

            df = pd.DataFrame([asdict(r) for r in all_records])

            # Keep your column ordering behavior
            cols = ["filename", "name", "role", "is_corresponding", "affiliation", "email"]
            final_cols = [c for c in cols if c in df.columns]
            df = df[final_cols]

            st.dataframe(df)

            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download as CSV",
                data=csv_bytes,
                file_name="authors_extracted.csv",
                mime="text/csv",
            )


# =========================
# Bootstrap
# =========================
def main():
    load_dotenv()

    model_id = "Llama-4-Maverick-17B-128E-Instruct"
    base_url = "https://api.sambanova.ai/v1"
    api_key = os.environ.get("SAMBANOVA_API_KEY", "")

    renderer = PdfRenderer(zoom=2.0)
    llm = LLMClient(base_url=base_url, api_key=api_key, model_id=model_id, temperature=0.1)
    service = AuthorExtractorService(renderer=renderer, llm=llm)
    temp_writer = TempPdfWriter(temp_path="temp_paper.pdf")

    app = StreamlitAuthorApp(extractor=service, temp_writer=temp_writer)
    app.run()


if __name__ == "__main__":
    main()
