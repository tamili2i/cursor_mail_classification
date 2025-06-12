# Email Analysis API (POC)

This is a FastAPI-based API for analyzing emails (EML or text) using a local LLM (Mistral via Ollama) and Prefect for orchestration.

## Requirements
- Python 3.8+
- Ollama running locally with the `mistral` model pulled
- Prefect
- 16GB RAM (recommended)

## Installation
```bash
pip install -r requirements.txt
```

## Ollama Setup
1. [Install Ollama](https://ollama.com/download)
2. Pull the mistral model:
   ```bash
   ollama pull mistral
   ```
3. Start Ollama (if not already running):
   ```bash
   ollama serve
   ```

## Running the API
```bash
uvicorn main:app --reload
```

## Usage
- Endpoint: `POST /analyze-email`
- Accepts either:
  - `eml_file`: An uploaded .eml file
  - `text`: Raw email text
- Response: JSON with classification and extracted purchase info

### Example (using curl)
```bash
curl -X POST "http://localhost:8000/analyze-email" \
  -F "eml_file=@sample.eml"

curl -X POST "http://localhost:8000/analyze-email" \
  -F "text=Your order for 2 widgets totaling $19.99 will ship to 123 Main St."
```

### Sample Response
```json
{
  "label": "Order",
  "extracted_content": {
    "products": ["widgets"],
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
```

## Running Unit Tests

This project uses `unittest` for testing. To run all tests:

```bash
python -m unittest test_main.py
```

## Checking Code Coverage

To check code coverage, install the `coverage` package if you haven't already:

```bash
pip install coverage
```

Run the tests with coverage:

```bash
coverage run --source=main -m unittest test_main.py
```

Generate a coverage report in the terminal:

```bash
coverage report -m
```

Generate an HTML coverage report:

```bash
coverage html
# Then open htmlcov/index.html in your browser
```

## Notes
- The API uses Prefect flows for orchestration and documentation.
- Ollama is called with temperature=0 for deterministic results.
- This is for POC/demo purposes only. 