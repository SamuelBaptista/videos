import io
import os
import base64
import math
import uuid
import boto3
import typing

import streamlit as st

from PIL import Image
from io import BytesIO
from docx import Document

from pdf2image import convert_from_bytes
from dotenv import load_dotenv

from prompts import (
    OCR_CLASSIFICATION, 
    OCR_PROMPT, 
    OCR_TABLES
)

from repenseai.genai.agent import Agent
from repenseai.genai.tasks.api import Task
from pydantic import BaseModel

from mistralai import Mistral

# Load environment variables from .env file
load_dotenv()

MISTRAL_CLIENT = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

class ClassificationResponse(BaseModel):
    classifications: list[str]


def extract_docx_text(docx_bytes: bytes):
    doc = Document(BytesIO(docx_bytes))
    text = []

    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text.append(paragraph.text)

    return "\n\n".join(text)


def extract_txt_text(txt_bytes: bytes):
    try:
        text = txt_bytes.decode("utf-8")
        return text
    except UnicodeDecodeError:
        return txt_bytes.decode("latin-1")


def textract_extract_text(image: bytes):
    textract = boto3.client(
        "textract",
        region_name="us-east-2",
    )

    response = textract.detect_document_text(Document={"Bytes": image})
    blocks = response["Blocks"]
    line_list = [block["Text"] for block in blocks if block["BlockType"] == "LINE"]
    return "\n".join(line_list)    


def format_openai_file(file_bytes: bytes, file_type: str):
    if file_type == "pdf":
        images = convert_from_bytes(file_bytes)
        image_data = []

        for image in images:
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            image_data.append(
                f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
            )

        return [{"type": "image_url", "image_url": {"url": img}} for img in image_data]
    elif file_type in ["png", "jpg", "jpeg"]:
        image = Image.open(BytesIO(file_bytes))
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        image_data = f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"

        return [{"type": "image_url", "image_url": {"url": image_data}}]
    elif file_type in ["txt", "docx"]:
        funcs = {"txt": extract_txt_text, "docx": extract_docx_text}
        text = funcs[file_type](file_bytes)

        return [{"type": "text", "text": text}]
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def format_openai_history(files: typing.List[bytes], types: typing.List[str]):
    history = {"role": "user", "content": []}
    for file, file_type in zip(files, types):
        history["content"].extend(format_openai_file(file, file_type))
    return [history]


def format_anthropic_file(file_bytes: bytes, file_type: str):
    if file_type == "pdf":
        return {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": base64.standard_b64encode(file_bytes).decode("utf-8"),
            },
        }
    elif file_type in ["txt", "docx"]:
        funcs = {"txt": extract_txt_text, "docx": extract_docx_text}

        text = funcs[file_type](file_bytes)

        return {"type": "text", "text": text}

    else:
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": f"image/{file_type}",
                "data": base64.standard_b64encode(file_bytes).decode("utf-8"),
            },
        }


def format_anthropic_history(files: typing.List[bytes], types: typing.List[str]):
    history = {"role": "user", "content": []}

    for file, type in zip(files, types):
        history["content"].append(format_anthropic_file(file, type))

    return [history]


def image_to_bytes(image: Image.Image) -> bytes:
    """Convert PIL Image to bytes."""
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    return img_byte_arr.getvalue()


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    output = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")
    return output


def base64_to_image(base64_string: str) -> Image.Image:
    """Convert base64 string to PIL Image."""
    if base64_string.startswith("data:image"):
        base64_string = base64_string.split(",")[1]
    image_bytes = base64.b64decode(base64_string)
    img_byte_arr = io.BytesIO(image_bytes)
    image = Image.open(img_byte_arr)
    return image


def classify_image(image: Image.Image) -> list[str]:
    """Classify the content type of an image."""
    agent = Agent(
        model="gpt-4.1",
        model_type="vision",
        json_schema=ClassificationResponse,
    )

    task = Task(
        user=OCR_CLASSIFICATION,
        agent=agent,
        simple_response=True,
    )

    try:
        response = task.run({"image": image})
        return response["classifications"]
    except Exception:
        return ["none"]


def mistral_ocr(image: Image.Image, model="mistral-ocr-2503"):
    """Process image with Mistral OCR."""
    image_b64 = image_to_base64(image)
    ocr_response = MISTRAL_CLIENT.ocr.process(
        model=model,
        include_image_base64=True,
        document={
            "type": "image_url",
            "image_url": f"data:image/png;base64,{image_b64}",
        },
    )
    return ocr_response


def anthropic_text_ocr(image: Image.Image):
    """Extract text from image using Anthropic."""
    agent = Agent(
        model="claude-sonnet-4-0",
        model_type="chat",
        provider="anthropic",
        price={"input": 3.0, "output": 15.0},
        temperature=0.0,
    )

    image_bytes = image_to_bytes(image)
    history = format_anthropic_history([image_bytes], ["png"])

    task = Task(
        user=OCR_PROMPT,
        agent=agent,
        simple_response=True,
        history=history,
    )

    try:
        response = task.run({"image": image})
        return response
    except Exception:
        return {"error": "Failed to process instructions"}


def anthropic_table_ocr(image: Image.Image):
    """Extract table from image using Anthropic."""
    agent = Agent(
        model="claude-sonnet-4-0",
        model_type="chat",
        thinking=True,
        provider="anthropic",
        price={"input": 3.0, "output": 15.0},
        temperature=0.0,
    )

    image_bytes = image_to_bytes(image)
    history = format_anthropic_history([image_bytes], ["png"])

    task = Task(
        user=OCR_TABLES,
        agent=agent,
        simple_response=True,
        history=history,
    )

    try:
        response = task.run({"image": image})
        return response["output"]
    except Exception:
        return {"error": "Failed to process instructions"}


def process_single_page_data(image: Image.Image, classifications: list[str]):
    """Process a single page based on its classifications."""
    results = {
        "text": None,
        "instructions": None,
        "table": None,
        "image_data": None,
    }

    if "text" in classifications:
        results["text"] = anthropic_text_ocr(image)

    if "instructions" in classifications:
        results["instructions"] = anthropic_text_ocr(image)

    if "table" in classifications:
        results["table"] = anthropic_table_ocr(image)

    if "image" in classifications:
        mistral_results = mistral_ocr(image)
        if mistral_results.pages:
            results["image_data"] = mistral_results.pages[0].images

    return results


def process_document(file_bytes: bytes, file_type: str) -> list[dict]:
    """
    Processes an uploaded document (PDF or image) and returns extracted data for each page.
    """
    if file_type == "application/pdf":
        images = convert_from_bytes(file_bytes)
    else:  # Assuming image type
        images = [Image.open(io.BytesIO(file_bytes))]

    if not images:
        return []

    if len(images) > 10:
        raise ValueError("Document cannot exceed 10 pages.")

    processed_pages_data = []
    for image in images:
        classifications = classify_image(image)
        if "none" in classifications:
            processed_pages_data.append({})
            continue

        page_data = process_single_page_data(image, classifications)
        processed_pages_data.append(page_data)

    return processed_pages_data


def resize_image_for_display(image: Image.Image) -> Image.Image:
    """
    Resize and process image according to publication specifications.
    This method is kept separate as it's more related to display logic
    that might still be needed by Streamlit, or a future frontend.
    """
    # Convert to RGB mode to remove transparency and flatten layers
    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(image, mask=image.split()[-1])
        image = background

    current_width, current_height = image.size
    MAX_WIDTH_PIXELS = 3300
    if current_width > MAX_WIDTH_PIXELS:
        aspect_ratio = current_height / current_width
        new_width = MAX_WIDTH_PIXELS
        new_height = math.floor(MAX_WIDTH_PIXELS * aspect_ratio)
        image = image.resize((new_width, new_height), Image.LANCZOS)

    image.info["dpi"] = (300, 300)
    return image


def display_images(images_data):
    """Display images in a grid layout with download buttons."""
    cols = st.columns(4)
    for idx, ocr_img_data in enumerate(images_data):
        try:
            image_bytes_pil = base64_to_image(ocr_img_data.image_base64)
        except AttributeError:
            st.error(
                "Image data format from service is not as expected for display_images."
            )
            continue

        image_id = str(uuid.uuid4())

        with cols[idx % 4]:
            st.image(image_bytes_pil, caption=f"Imagem {idx + 1}")
            resized_pil_image = resize_image_for_display(image_bytes_pil)

            download_image_bytes = image_to_bytes(resized_pil_image)

            st.download_button(
                label="Download",
                data=download_image_bytes,
                file_name=f"{image_id}.png",
                mime="image/png",
                key=f"download_{image_id}_{idx}",
            )


def display_results(results: dict, page_index: int = None, pages_images: list = None):
    """Display OCR results with optional page image."""
    # Get the current page image if page_index is provided
    current_page_image = None
    if page_index is not None and pages_images:
        if 0 <= page_index < len(pages_images):
            current_page_image = pages_images[page_index]

    # Check if we have any text content (either text or instructions)
    text_content = results.get("text") or results.get("instructions")

    if text_content and current_page_image is not None:
        # Two columns: text content and page image
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📝 Extracted Text")
            st.text(text_content)

            # Determine the download filename and key based on content type
            if results.get("text"):
                filename = "extracted_text.txt"
                key = "download_text_results"
            else:
                filename = "extracted_instructions.txt"
                key = "download_instructions_results"

            st.download_button(
                label="Download Text",
                data=str(text_content),
                file_name=filename,
                mime="text/plain",
                key=key,
            )

        with col2:
            st.subheader("📄 PDF Page")
            st.image(
                current_page_image,
                caption=f"Page {page_index + 1}",
                use_container_width=True,
            )

        st.divider()

    elif text_content:
        # Only text content, no page image
        st.subheader("📝 Extracted Text")
        st.text(text_content)

        # Determine the download filename and key based on content type
        if results.get("text"):
            filename = "extracted_text.txt"
            key = "download_text_results"
        else:
            filename = "extracted_instructions.txt"
            key = "download_instructions_results"

        st.download_button(
            label="Download Text",
            data=str(text_content),
            file_name=filename,
            mime="text/plain",
            key=key,
        )
        st.divider()

    elif current_page_image is not None:
        # Only page image, no text content
        st.info("PDF Page")
        st.image(
            current_page_image,
            caption=f"Page {page_index + 1}",
            use_container_width=True,
        )
        st.divider()

    if results.get("table"):
        st.subheader("📊 Table Content")
        st.markdown(results["table"], unsafe_allow_html=True)

        st.download_button(
            label="Download Table as HTML",
            data=results["table"],
            file_name="table.html",
            mime="text/html",
            key="download_table_results",
        )

        st.divider()

    if results.get("image_data"):
        st.subheader("🖼️ Extracted Images")
        display_images(results["image_data"])
