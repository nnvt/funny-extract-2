import base64
import fitz  # PyMuPDF


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


class TempPdfWriter:
    """Writes an uploaded file to a stable temp path (single-file reuse)."""

    def __init__(self, temp_path: str = "temp_paper.pdf"):
        self.temp_path = temp_path

    def write(self, uploaded_file) -> str:
        with open(self.temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return self.temp_path
