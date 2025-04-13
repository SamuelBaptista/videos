import os
import requests

root_url = "https://api.bland.ai/v1/calls"
BLAND_API_KEY = os.getenv("BLAND_API_KEY")


def make_blandai_call(prompt: str, phone_number: str, parameters: dict) -> dict:

    payload = {
        "phone_number": phone_number,
        "task": prompt,
        "voice": "paige",
        "wait_for_greeting": True,
        "model": "enhanced",
        "temperature": 0.0,
        "interruption_threshold": 150,
        "language": "pt-BR",
        # "language_detection_period": 10,
        # "language_detection_options": ["en-US", "en-IN", "es-419", "pt-BR"],
        "max_duration": 5,
        "request_data": parameters,
        "record": True,
        "background_track": "office",
    }

    headers = {"authorization": BLAND_API_KEY, "Content-Type": "application/json"}
    response = requests.post(root_url, json=payload, headers=headers)

    return response.json()   


def get_call_info(call_id: str) -> dict:
    headers = {"authorization": BLAND_API_KEY, "Content-Type": "application/json"}

    info_url = f"{root_url}/{call_id}"
    response = requests.get(url=info_url, headers=headers)

    return response.json()

