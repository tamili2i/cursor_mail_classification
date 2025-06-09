from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import Optional
import email
from email import policy
from email.parser import BytesParser
import requests
import os
import logging

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = "mistral"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

def parse_eml(file_bytes: bytes) -> str:
    msg = BytesParser(policy=policy.default).parsebytes(file_bytes)
    if msg.is_multipart():
        parts = [part.get_payload(decode=True) for part in msg.walk() if part.get_content_type() == 'text/plain']
        text = b"\n".join([p for p in parts if p]).decode(errors="ignore")
    else:
        text = msg.get_payload(decode=True).decode(errors="ignore")
    return text

def call_ollama(prompt: str) -> dict:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "options": {"temperature": 0}
    }
    response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
    response.raise_for_status()
    # Ollama streams output, so get the last line with 'response' key
    lines = response.text.strip().split("\n")
    for line in reversed(lines):
        if 'response' in line:
            import json as js
            try:
                data = js.loads(line)
                return data.get('response', '').strip()
            except Exception:
                continue
    return ""

def analyze_email_logic(email_text: str) -> dict:
    # Prompt for extraction and classification
    prompt = f"""
You are an email analysis assistant. Analyze the following email and:
1. Classify it as one of: Offer, Order, Account, Refund, Receipt, OTP.
2. Extract purchase information: products (list), amount (number), shipping address (string). If not present, use null or empty.

Respond ONLY in JSON with keys: label, extracted content (with products, amount, shipping_address).

Example output:
{{"label": "Order", "extracted content": {{"products": ["Widget"], "amount": 19.99, "shipping_address": "123 Main St."}}}}

Email:
"""
    prompt += email_text
    print(prompt)
    result = call_ollama(prompt)
    logger.debug(result)
    # Try to parse JSON from result
    import json
    try:
        parsed = json.loads(result)
        return parsed
    except Exception:
        # fallback: return as string
        return {"label": "Unknown", "extracted content": {}, "raw": result}

@app.post("/analyze-email")
def analyze_email(
    eml_file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None)
):
    if eml_file:
        file_bytes = eml_file.file.read()
        email_text = parse_eml(file_bytes)
    elif text:
        email_text = text
    else:
        return JSONResponse({"error": "No input provided"}, status_code=400)
    result = analyze_email_logic(email_text)
    logger.debug(result)
    return JSONResponse(result) 