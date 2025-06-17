package com.example.emailanalyzer.model;

import lombok.Data;

@Data
public class EmailAnalysisResponse {
    private String label;
    private ExtractedContent extractedContent;
    private String raw;
} 