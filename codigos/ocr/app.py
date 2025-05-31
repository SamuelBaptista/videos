import io
import streamlit as st

from pdf2image import convert_from_bytes
from PIL import Image

from functions import (
    process_document,
    display_results,
)

st.set_page_config(
    page_title="OCR - RepenseAI", 
    page_icon=":robot:", 
    layout="wide"
)


if "pages_images" not in st.session_state:
    st.session_state["pages_images"] = []

if "processed_results" not in st.session_state:
    st.session_state["processed_results"] = []


st.title("OCR")
st.subheader("Optical Character Recognition")

st.text(
    "Upload your files below and have images, tables and text extracted.\n(Logos and signatures are not considered as images)"
)

uploaded_file = st.file_uploader(
    "Upload document (PDF, PNG, JPG)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=False,
)

if st.button("Process Document"):
    if uploaded_file is None:
        st.error("Please upload a document first.")
        st.stop()

    st.session_state["processed_results"] = []
    st.session_state["pages_images"] = []

    file_bytes = uploaded_file.read()
    file_type = uploaded_file.type

    if file_type == "application/pdf":
        st.session_state["pages_images"] = convert_from_bytes(file_bytes)
    else:
        st.session_state["pages_images"] = [Image.open(io.BytesIO(file_bytes))]

    if len(st.session_state["pages_images"]) > 10:
        st.error("Please upload a document up to 10 pages.")
        st.stop()

    with st.spinner("Processing document..."):
        try:
            processed_data_list = process_document(file_bytes, file_type)
            st.session_state["processed_results"] = processed_data_list

            if not processed_data_list:
                st.warning(
                    "No data was extracted from the document or all pages were classified as 'none'."
                )
            elif all(not page_data for page_data in processed_data_list):
                st.warning(
                    "All pages were classified as 'none' or no extractable content was found."
                )

        except ValueError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            print(f"Error during OCR processing: {e}")
            st.stop()

st.divider()

results_to_display = [res for res in st.session_state["processed_results"] if res]

if results_to_display:
    pages_with_results_indices = [
        idx for idx, res in enumerate(st.session_state["processed_results"]) if res
    ]

    if not pages_with_results_indices:
        st.info("No pages with extractable content found after processing.")
    else:
        page_selector_options = {
            f"Page {original_idx + 1}": actual_idx
            for actual_idx, original_idx in enumerate(pages_with_results_indices)
        }

        selected_page_label = st.selectbox(
            "Select a page to view results",
            options=list(page_selector_options.keys()),
            key="page_selector",
        )
        st.divider()

        if selected_page_label is not None:
            selected_display_idx = page_selector_options[selected_page_label]
            current_results_to_display = results_to_display[selected_display_idx]
            original_page_idx = pages_with_results_indices[selected_display_idx]

            display_results(
                current_results_to_display,
                original_page_idx,
                st.session_state["pages_images"],
            )

elif st.session_state["processed_results"] and not results_to_display:
    st.info(
        "The document was processed, but no pages yielded extractable content based on classifications."
    )
