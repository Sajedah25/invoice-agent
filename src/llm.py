import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODELS = [
    os.environ["GEMINI_MODEL"],
    os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash"),
]
RETRIES_PER_MODEL = 3
TEMPORARY_ERRORS = {429, 500, 503}


class LLMUnavailable(Exception):
    pass


def generate_json(prompt, schema_model):
    for model in MODELS:
        for attempt in range(RETRIES_PER_MODEL):
            try:
                response = _client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_json_schema": schema_model.model_json_schema(),
                    },
                )
                return response.text
            except errors.APIError as e:
                if e.code not in TEMPORARY_ERRORS:
                    raise
                wait = 5 * 2**attempt
                print(f"  {model} unavailable ({e.code}), retrying in {wait}s...")
                time.sleep(wait)
        print(f"  {model} kept failing, switching to the next model")
    raise LLMUnavailable("All models are unavailable right now")