from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import Optional
from email import policy
from email.parser import BytesParser
import requests
import os
import logging
import re
import json

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

def call_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "options": {"temperature": 0}
    }
    response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
    response.raise_for_status()
    lines = response.text.strip().split("\n")
    # Collect all response fragments
    response_fragments = []
    for line in lines:
        try:
            data = json.loads(line)
            fragment = data.get('response', '')
            response_fragments.append(fragment)
        except Exception as e:
            logging.error(f"JSON decode error: {e} for line: {line}")
    full_response = ''.join(response_fragments).strip()
    # logging.info(f"Full LLM response: {full_response}")
    return full_response

def extract_json_from_response(response_text):
    # Try to find the first {...} block
    match = re.search(r'({.*})', response_text, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except Exception as e:
            logging.error(f"JSON decode error: {e}\nJSON string: {json_str}")
            return None
    logging.error("No JSON object found in response.")
    return None

def analyze_email_logic(email_text: str) -> dict:
    # Prompt for extraction and classification
    prompt = (
        """
You are an email analysis assistant. Analyze the following email and:
1. Classify it as one of: Offer, Order, Account, Refund, Receipt, OTP.
2. Extract purchase information:
   - products (list)
   - amount (number)
   - shipping_address (object with: address_line1, address_line2, city, state, pincode, phone_number)
   - billing_address (object with: address_line1, address_line2, city, state, pincode, phone_number)
If any field is missing, use null or empty.

Respond ONLY in JSON with keys: label, extracted_content (with products, amount, shipping_address, billing_address).

Example output:
{
  "label": "Order",
  "extracted_content": {
    "products": ["Widget"],
    "amount": 19.99,
    "shipping_address": {
      "address_line1": "123 Main St.",
      "address_line2": "Apt 4B",
      "city": "Springfield",
      "state": "IL",
      "pincode": "62704",
      "phone_number": "555-123-4567"
    },
    "billing_address": {
      "address_line1": "123 Main St.",
      "address_line2": "Apt 4B",
      "city": "Springfield",
      "state": "IL",
      "pincode": "62704",
      "phone_number": "555-123-4567"
    }
  }
}

Email:
"""
        + email_text
    )
    result = call_ollama(prompt)
    logging.info(f"Full LLM response: {result}")
    parsed = extract_json_from_response(result)
    if parsed:
        # If the model returns 'extracted content', convert to 'extracted_content' for consistency
        if 'extracted_content' in parsed:
            parsed['extracted_content'] = parsed.pop('extracted_content')
        return parsed
    else:
        return {"label": "Unknown", "extracted_content": {}, "raw": result}

@app.post("/analyze-email")
def analyze_email(
    eml_file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None)
):
    if eml_file and text:
        return JSONResponse({"error": "Provide only one of eml_file or text, not both."}, status_code=400)
    if eml_file:
        file_bytes = eml_file.file.read()
        email_text = parse_eml(file_bytes)
    elif text:
        email_text = text
    else:
        return JSONResponse({"error": "No input provided"}, status_code=400)
    result = analyze_email_logic(email_text)
    return JSONResponse(result) 