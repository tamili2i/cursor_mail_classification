from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class PaymentResult:
    """Data class to hold payment processing results."""
    success: bool
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None


class PaymentStrategy(ABC):
    """Abstract base class for payment strategies."""
    
    @abstractmethod
    def process_payment(self, amount: Decimal, currency: str, **kwargs) -> PaymentResult:
        """
        Process a payment using the specific payment strategy.
        
        Args:
            amount: The payment amount
            currency: The currency code (e.g., 'USD', 'EUR')
            **kwargs: Additional payment-specific parameters
            
        Returns:
            PaymentResult: The result of the payment processing
        """
        pass
    
    @abstractmethod
    def refund_payment(self, transaction_id: str, amount: Decimal, **kwargs) -> PaymentResult:
        """
        Process a refund for a previous payment.
        
        Args:
            transaction_id: The original transaction ID
            amount: The amount to refund
            **kwargs: Additional refund-specific parameters
            
        Returns:
            PaymentResult: The result of the refund processing
        """
        pass 