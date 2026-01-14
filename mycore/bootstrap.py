import os
from dotenv import load_dotenv

from .pdf import PdfRenderer, TempPdfWriter
from .llm import LLMClient
from .service import AuthorExtractorService
from .ui import StreamlitAuthorApp


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
