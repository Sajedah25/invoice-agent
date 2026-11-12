import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.environ["GEMINI_MODEL"]


def generate_json(prompt, schema_model):
    response = _client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": schema_model.model_json_schema(),
        },
    )
    return response.text