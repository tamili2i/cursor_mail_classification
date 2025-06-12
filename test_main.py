import unittest
from unittest.mock import patch, MagicMock
from main import analyze_email_logic, parse_eml, extract_json_from_response, app
from fastapi.testclient import TestClient
import json

client = TestClient(app)

class TestUtils(unittest.TestCase):
    def test_parse_eml_non_multipart(self):
        # Create a simple non-multipart email
        from email.message import EmailMessage
        msg = EmailMessage()
        msg.set_content("This is a test email body.")
        eml_bytes = msg.as_bytes()
        result = parse_eml(eml_bytes)
        self.assertIn("This is a test email body.", result)

    def test_parse_eml_multipart(self):
        # Create a multipart email
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        msg = MIMEMultipart()
        msg.attach(MIMEText("This is the plain text part.", "plain"))
        eml_bytes = msg.as_bytes()
        result = parse_eml(eml_bytes)
        self.assertIn("This is the plain text part.", result)

    def test_extract_json_from_response_valid(self):
        json_str = '{"label": "Order", "extracted_content": {}}'
        result = extract_json_from_response(json_str)
        self.assertEqual(result['label'], "Order")

    def test_extract_json_from_response_invalid(self):
        result = extract_json_from_response("not a json")
        self.assertIsNone(result)

    def test_extract_json_from_response_json_exception(self):
        # This string has curly braces but is not valid JSON inside
        malformed = '{label: Order, extracted_content: }'
        result = extract_json_from_response(malformed)
        self.assertIsNone(result)

    @patch('main.call_ollama')
    def test_analyze_email_logic_positive(self, mock_call_ollama):
        # Mock call_ollama to return a valid JSON string
        mock_call_ollama.return_value = '{"label": "Order", "extracted_content": {"products": ["Widget"], "amount": 19.99}}'
        email_text = "Order confirmation for Widget."
        result = analyze_email_logic(email_text)
        self.assertEqual(result['label'], 'Order')
        self.assertIn('extracted_content', result)
        self.assertEqual(result['extracted_content']['products'], ["Widget"])
        self.assertEqual(result['extracted_content']['amount'], 19.99)

    @patch('main.call_ollama')
    def test_analyze_email_logic_negative(self, mock_call_ollama):
        # Mock call_ollama to return an invalid JSON string
        mock_call_ollama.return_value = 'not a json string'
        email_text = "Order confirmation for Widget."
        result = analyze_email_logic(email_text)
        self.assertEqual(result['label'], 'Unknown')
        self.assertEqual(result['extracted_content'], {})
        self.assertIn('raw', result)

class TestAPI(unittest.TestCase):
    @patch('main.analyze_email_logic')
    def test_api_both_inputs(self, mock_logic):
        response = client.post("/analyze-email", data={"text": "test"}, files={"eml_file": ("test.eml", b"test")})
        self.assertEqual(response.status_code, 400)
        self.assertIn("not both", response.json()["error"])

    @patch('main.analyze_email_logic')
    def test_api_no_input(self, mock_logic):
        response = client.post("/analyze-email", data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("No input provided", response.json()["error"])

    @patch('main.analyze_email_logic')
    def test_api_text_input(self, mock_logic):
        mock_logic.return_value = {"label": "Order", "extracted_content": {}}
        response = client.post("/analyze-email", data={"text": "Order email"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["label"], "Order")

    @patch('main.analyze_email_logic')
    def test_api_eml_input(self, mock_logic):
        mock_logic.return_value = {"label": "Order", "extracted_content": {}}
        response = client.post("/analyze-email", files={"eml_file": ("test.eml", b"test")})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["label"], "Order")

def test_analyze_email_logic_with_partial_json():
    # Simulate a response with extra text before/after JSON
    with patch('main.call_ollama', return_value='Some intro text { "label": "Order", "extracted_content": {} } Some trailing text'):
        result = analyze_email_logic("Order email")
        assert result['label'] == "Order"

def test_call_ollama_success():
    from main import call_ollama
    # Simulate Ollama's streaming response
    fake_response = (
        json.dumps({"response": '{"label": "Order", "extracted_content": {}}', "done": False}) + "\n" +
        json.dumps({"response": "", "done": True})
    )
    mock_post = MagicMock()
    mock_post.return_value.text = fake_response
    mock_post.return_value.raise_for_status = lambda: None

    with patch('main.requests.post', mock_post):
        result = call_ollama("dummy prompt")
        assert '{"label": "Order", "extracted_content": {}}' in result

def test_call_ollama_json_decode_error():
    from main import call_ollama
    # Simulate a malformed JSON line in the response
    fake_response = 'not a json\n'
    mock_post = MagicMock()
    mock_post.return_value.text = fake_response
    mock_post.return_value.raise_for_status = lambda: None

    with patch('main.requests.post', mock_post):
        result = call_ollama("dummy prompt")
        assert result == ""

if __name__ == '__main__':
    unittest.main() 