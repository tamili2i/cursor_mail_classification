package com.example.emailanalyzer.service;

import com.example.emailanalyzer.model.EmailAnalysisResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import javax.mail.MessagingException;
import javax.mail.Session;
import javax.mail.internet.MimeMessage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.Properties;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class EmailAnalysisService {

    @Value("${ollama.url:http://localhost:11434}")
    private String ollamaUrl;

    private static final String OLLAMA_MODEL = "mistral";
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    public EmailAnalysisService() {
        this.restTemplate = new RestTemplate();
        this.objectMapper = new ObjectMapper();
    }

    public String parseEml(byte[] fileBytes) throws MessagingException, IOException {
        Properties props = new Properties();
        Session session = Session.getDefaultInstance(props, null);
        MimeMessage message = new MimeMessage(session, new ByteArrayInputStream(fileBytes));
        
        StringBuilder text = new StringBuilder();
        if (message.isMimeType("multipart/*")) {
            // Handle multipart message
            javax.mail.Multipart multipart = (javax.mail.Multipart) message.getContent();
            for (int i = 0; i < multipart.getCount(); i++) {
                javax.mail.BodyPart bodyPart = multipart.getBodyPart(i);
                if (bodyPart.isMimeType("text/plain")) {
                    text.append(bodyPart.getContent().toString());
                }
            }
        } else {
            // Handle single part message
            text.append(message.getContent().toString());
        }
        return text.toString();
    }

    private String callOllama(String prompt) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        String requestBody = String.format(
            "{\"model\": \"%s\", \"prompt\": \"%s\", \"options\": {\"temperature\": 0}}",
            OLLAMA_MODEL, prompt
        );

        HttpEntity<String> request = new HttpEntity<>(requestBody, headers);
        return restTemplate.postForObject(ollamaUrl + "/api/generate", request, String.class);
    }

    private EmailAnalysisResponse extractJsonFromResponse(String responseText) {
        Pattern pattern = Pattern.compile("(\\{.*\\})", Pattern.DOTALL);
        Matcher matcher = pattern.matcher(responseText);
        
        if (matcher.find()) {
            String jsonStr = matcher.group(1);
            try {
                return objectMapper.readValue(jsonStr, EmailAnalysisResponse.class);
            } catch (IOException e) {
                // Log error
                return createErrorResponse("JSON decode error: " + e.getMessage(), responseText);
            }
        }
        return createErrorResponse("No JSON object found in response.", responseText);
    }

    private EmailAnalysisResponse createErrorResponse(String error, String raw) {
        EmailAnalysisResponse response = new EmailAnalysisResponse();
        response.setLabel("Unknown");
        response.setRaw(raw);
        return response;
    }

    public EmailAnalysisResponse analyzeEmail(String emailText) {
        String prompt = """
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
            """ + emailText;

        String result = callOllama(prompt);
        return extractJsonFromResponse(result);
    }
} 