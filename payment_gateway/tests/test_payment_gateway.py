import pytest
from decimal import Decimal

from app.payment_gateway.payment_strategy import PaymentResult
from app.payment_gateway.concrete_strategies import CreditCardStrategy, PayPalStrategy
from app.payment_gateway.payment_gateway import PaymentGateway


class TestPaymentGateway:
    @pytest.fixture
    def credit_card_strategy(self):
        return CreditCardStrategy(api_key="test_key", merchant_id="test_merchant")
    
    @pytest.fixture
    def paypal_strategy(self):
        return PayPalStrategy(client_id="test_client", client_secret="test_secret")
    
    @pytest.fixture
    def payment_gateway(self, credit_card_strategy):
        return PaymentGateway(credit_card_strategy)
    
    def test_credit_card_payment_success(self, payment_gateway):
        # Test successful credit card payment
        result = payment_gateway.process_payment(
            amount=Decimal("100.00"),
            currency="USD",
            card_number="4111111111111111",
            expiry_date="12/25",
            cvv="123"
        )
        
        assert result.success is True
        assert result.transaction_id.startswith("CC-")
        assert result.error_message is None
    
    def test_credit_card_payment_failure(self, payment_gateway):
        # Test credit card payment with missing details
        result = payment_gateway.process_payment(
            amount=Decimal("100.00"),
            currency="USD"
        )
        
        assert result.success is False
        assert result.transaction_id is None
        assert result.error_message == "Missing required card details"
    
    def test_paypal_payment_success(self, payment_gateway, paypal_strategy):
        # Switch to PayPal strategy
        payment_gateway.set_payment_strategy(paypal_strategy)
        
        result = payment_gateway.process_payment(
            amount=Decimal("100.00"),
            currency="USD",
            paypal_email="test@example.com"
        )
        
        assert result.success is True
        assert result.transaction_id.startswith("PP-")
        assert result.error_message is None
    
    def test_paypal_payment_failure(self, payment_gateway, paypal_strategy):
        # Switch to PayPal strategy
        payment_gateway.set_payment_strategy(paypal_strategy)
        
        result = payment_gateway.process_payment(
            amount=Decimal("100.00"),
            currency="USD"
        )
        
        assert result.success is False
        assert result.transaction_id is None
        assert result.error_message == "PayPal email is required"
    
    def test_credit_card_refund(self, payment_gateway):
        # Test credit card refund
        result = payment_gateway.refund_payment(
            transaction_id="CC-12345678",
            amount=Decimal("50.00")
        )
        
        assert result.success is True
        assert result.transaction_id == "REF-CC-12345678"
        assert result.error_message is None
    
    def test_paypal_refund(self, payment_gateway, paypal_strategy):
        # Switch to PayPal strategy
        payment_gateway.set_payment_strategy(paypal_strategy)
        
        result = payment_gateway.refund_payment(
            transaction_id="PP-12345678",
            amount=Decimal("50.00")
        )
        
        assert result.success is True
        assert result.transaction_id == "REF-PP-12345678"
        assert result.error_message is None 