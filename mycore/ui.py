import streamlit as st
import pandas as pd
import time
from typing import List
from dataclasses import asdict

from .models import AuthorRecord


class StreamlitAuthorApp:
    def __init__(self, extractor, temp_writer):
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
