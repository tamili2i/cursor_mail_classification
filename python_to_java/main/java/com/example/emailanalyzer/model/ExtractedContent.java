package com.example.emailanalyzer.model;

import lombok.Data;
import java.util.List;

@Data
public class ExtractedContent {
    private List<String> products;
    private Double amount;
    private Address shippingAddress;
    private Address billingAddress;
} 