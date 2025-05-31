import os
import base64

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="OCR Results Evaluation", 
    page_icon=":mag_right:", 
    layout="wide"
)

# Constants
RESULTS_PATH = "data/ocr_results.csv"

# Initialize session state
if "ocr_responses" not in st.session_state:
    st.session_state.ocr_responses = []

# Load existing results if available
if os.path.exists(RESULTS_PATH):
    existing_results = pd.read_csv(RESULTS_PATH)
    st.session_state.ocr_responses = existing_results.to_dict("records")

st.title("OCR Results Evaluation")

# Results Analysis Section
if st.session_state.ocr_responses:
    st.markdown("## OCR Results Analysis")
    results_df = pd.DataFrame(st.session_state.ocr_responses)

    # Calculate accuracy per model
    st.markdown("### Model Performance")
    model_metrics = []

    for model_name in results_df["model_name"].unique():
        model_df = results_df[results_df["model_name"] == model_name]
        accuracy_df = model_df[model_df["accuracy_score"].notna()]
        similarity_df = model_df[model_df["similarity_score"].notna()]

        if len(accuracy_df) > 0:
            accuracy = accuracy_df["accuracy_score"].mean()
        else:
            accuracy = None

        if len(similarity_df) > 0:
            similarity_score = similarity_df["similarity_score"].mean()
        else:
            similarity_score = None

        total_samples = len(model_df)
        evaluated_samples = len(accuracy_df)

        # Calculate average cost
        average_cost = model_df["cost"].mean() if "cost" in model_df.columns else 0.0

        model_metrics.append(
            {
                "Model": model_name,
                "Similarity Score": similarity_score,
                "Evaluated Samples": evaluated_samples,
                "Average Cost": f"${average_cost:.5f}",
            }
        )

    st.dataframe(pd.DataFrame(model_metrics), hide_index=True)

    st.divider()

    # Detailed Results
    st.markdown("## Detailed Results")

    # Filters
    available_models = results_df["model_name"].unique()
    selected_model = st.selectbox("Filter by Model", list(available_models))

    # Apply filters
    filtered_df = results_df.copy()
    filtered_df = filtered_df[filtered_df["model_name"] == selected_model]

    # Display results
    st.markdown("### Results Table")
    display_df = filtered_df[
        [
            "file_name",
            "model_name",
            "accuracy_score",
            "similarity_score",
            "explanation",
            "cost",
        ]
    ]
    st.dataframe(display_df, hide_index=True)

    st.divider()
    st.markdown("## Detailed View")

    # Detailed view section
    selected_file = st.selectbox(
        "Select file to view details", options=filtered_df["file_name"].unique()
    )

    if selected_file:
        file_result = filtered_df[filtered_df["file_name"] == selected_file].iloc[0]

        # Show original image and extracted text
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### Original Image")
            if file_result.get("image_data"):
                img_bytes = base64.b64decode(file_result["image_data"])
                st.image(img_bytes)
            else:
                st.info("Original image not available")

        with col2:
            st.markdown("#### Extracted Text")
            st.text(file_result["extracted_text"])

        with col3:
            st.markdown("#### Evaluation")
            if file_result.get("accuracy_score") == 0:
                st.markdown(file_result.get("evaluation_diff", "No evaluation available"))
            else:
                st.success("No differences found")
else:
    st.info("No OCR results found. Please ensure the results CSV file exists at: " + RESULTS_PATH)
