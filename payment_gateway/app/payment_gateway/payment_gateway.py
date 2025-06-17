from decimal import Decimal
from typing import Optional

from .payment_strategy import PaymentStrategy, PaymentResult


class PaymentGateway:
    """
    Payment Gateway client that uses different payment strategies.
    This class implements the Strategy pattern by allowing different
    payment methods to be used interchangeably.
    """
    
    def __init__(self, payment_strategy: PaymentStrategy):
        """
        Initialize the payment gateway with a specific payment strategy.
        
        Args:
            payment_strategy: The payment strategy to use
        """
        self._payment_strategy = payment_strategy
    
    def set_payment_strategy(self, payment_strategy: PaymentStrategy) -> None:
        """
        Change the payment strategy at runtime.
        
        Args:
            payment_strategy: The new payment strategy to use
        """
        self._payment_strategy = payment_strategy
    
    def process_payment(self, amount: Decimal, currency: str, **kwargs) -> PaymentResult:
        """
        Process a payment using the current payment strategy.
        
        Args:
            amount: The payment amount
            currency: The currency code
            **kwargs: Additional payment-specific parameters
            
        Returns:
            PaymentResult: The result of the payment processing
        """
        return self._payment_strategy.process_payment(amount, currency, **kwargs)
    
    def refund_payment(self, transaction_id: str, amount: Decimal, **kwargs) -> PaymentResult:
        """
        Process a refund using the current payment strategy.
        
        Args:
            transaction_id: The original transaction ID
            amount: The amount to refund
            **kwargs: Additional refund-specific parameters
            
        Returns:
            PaymentResult: The result of the refund processing
        """
        return self._payment_strategy.refund_payment(transaction_id, amount, **kwargs) 