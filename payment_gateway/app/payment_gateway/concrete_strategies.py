from decimal import Decimal
import uuid
from typing import Optional

from .payment_strategy import PaymentStrategy, PaymentResult


class CreditCardStrategy(PaymentStrategy):
    """Credit card payment strategy implementation."""
    
    def __init__(self, api_key: str, merchant_id: str):
        self.api_key = api_key
        self.merchant_id = merchant_id
    
    def process_payment(self, amount: Decimal, currency: str, **kwargs) -> PaymentResult:
        """
        Process a credit card payment.
        
        Args:
            amount: The payment amount
            currency: The currency code
            **kwargs: Must include 'card_number', 'expiry_date', 'cvv'
        """
        try:
            # In a real implementation, this would integrate with a payment processor
            # For demonstration, we'll simulate a successful payment
            card_number = kwargs.get('card_number')
            expiry_date = kwargs.get('expiry_date')
            cvv = kwargs.get('cvv')
            
            if not all([card_number, expiry_date, cvv]):
                return PaymentResult(
                    success=False,
                    error_message="Missing required card details"
                )
            
            # Simulate payment processing
            transaction_id = f"CC-{uuid.uuid4().hex[:8]}"
            return PaymentResult(
                success=True,
                transaction_id=transaction_id
            )
            
        except Exception as e:
            return PaymentResult(
                success=False,
                error_message=str(e)
            )
    
    def refund_payment(self, transaction_id: str, amount: Decimal, **kwargs) -> PaymentResult:
        """Process a refund for a credit card payment."""
        try:
            # Simulate refund processing
            return PaymentResult(
                success=True,
                transaction_id=f"REF-{transaction_id}"
            )
        except Exception as e:
            return PaymentResult(
                success=False,
                error_message=str(e)
            )


class PayPalStrategy(PaymentStrategy):
    """PayPal payment strategy implementation."""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    def process_payment(self, amount: Decimal, currency: str, **kwargs) -> PaymentResult:
        """
        Process a PayPal payment.
        
        Args:
            amount: The payment amount
            currency: The currency code
            **kwargs: Must include 'paypal_email'
        """
        try:
            paypal_email = kwargs.get('paypal_email')
            
            if not paypal_email:
                return PaymentResult(
                    success=False,
                    error_message="PayPal email is required"
                )
            
            # Simulate PayPal payment processing
            transaction_id = f"PP-{uuid.uuid4().hex[:8]}"
            return PaymentResult(
                success=True,
                transaction_id=transaction_id
            )
            
        except Exception as e:
            return PaymentResult(
                success=False,
                error_message=str(e)
            )
    
    def refund_payment(self, transaction_id: str, amount: Decimal, **kwargs) -> PaymentResult:
        """Process a refund for a PayPal payment."""
        try:
            # Simulate PayPal refund processing
            return PaymentResult(
                success=True,
                transaction_id=f"REF-{transaction_id}"
            )
        except Exception as e:
            return PaymentResult(
                success=False,
                error_message=str(e)
            ) 