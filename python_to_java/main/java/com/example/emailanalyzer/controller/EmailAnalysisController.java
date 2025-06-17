package com.example.emailanalyzer.controller;

import com.example.emailanalyzer.model.EmailAnalysisResponse;
import com.example.emailanalyzer.service.EmailAnalysisService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import javax.mail.MessagingException;

@RestController
@RequestMapping("/api")
public class EmailAnalysisController {

    private final EmailAnalysisService emailAnalysisService;

    @Autowired
    public EmailAnalysisController(EmailAnalysisService emailAnalysisService) {
        this.emailAnalysisService = emailAnalysisService;
    }

    @PostMapping("/analyze-email")
    public ResponseEntity<?> analyzeEmail(
            @RequestParam(value = "eml_file", required = false) MultipartFile emlFile,
            @RequestParam(value = "text", required = false) String text) {
        
        if (emlFile != null && text != null) {
            return ResponseEntity.badRequest().body("Provide only one of eml_file or text, not both.");
        }
        
        if (emlFile == null && text == null) {
            return ResponseEntity.badRequest().body("No input provided");
        }

        try {
            String emailText;
            if (emlFile != null) {
                emailText = emailAnalysisService.parseEml(emlFile.getBytes());
            } else {
                emailText = text;
            }
            
            EmailAnalysisResponse result = emailAnalysisService.analyzeEmail(emailText);
            return ResponseEntity.ok(result);
            
        } catch (IOException | MessagingException e) {
            return ResponseEntity.badRequest().body("Error processing email: " + e.getMessage());
        }
    }
} 