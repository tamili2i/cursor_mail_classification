# Payment Gateway with Strategy Pattern

A flexible payment gateway implementation using the Strategy pattern in Python. This implementation allows for easy addition of new payment methods and runtime switching between different payment strategies.

## Features

- Abstract payment strategy interface
- Concrete implementations for Credit Card and PayPal
- Easy to extend with new payment methods
- Runtime strategy switching
- Comprehensive unit tests
- Type hints and documentation

## Project Structure

```
payment_gateway/
├── app/
│   └── payment_gateway/
│       ├── payment_strategy.py    # Abstract strategy interface
│       ├── concrete_strategies.py # Concrete implementations
│       └── payment_gateway.py     # Client class
├── tests/
│   └── test_payment_gateway.py    # Unit tests
├── requirements.txt               # Project dependencies
└── README.md                     # This file
```

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage Example

```python
from decimal import Decimal
from app.payment_gateway.concrete_strategies import CreditCardStrategy, PayPalStrategy
from app.payment_gateway.payment_gateway import PaymentGateway

# Initialize with credit card strategy
credit_card = CreditCardStrategy(api_key="your_api_key", merchant_id="your_merchant_id")
gateway = PaymentGateway(credit_card)

# Process a credit card payment
result = gateway.process_payment(
    amount=Decimal("100.00"),
    currency="USD",
    card_number="4111111111111111",
    expiry_date="12/25",
    cvv="123"
)

# Switch to PayPal strategy
paypal = PayPalStrategy(client_id="your_client_id", client_secret="your_client_secret")
gateway.set_payment_strategy(paypal)

# Process a PayPal payment
result = gateway.process_payment(
    amount=Decimal("100.00"),
    currency="USD",
    paypal_email="customer@example.com"
)
```

## Running Tests

```bash
pytest
```

## Why Strategy Pattern?

The Strategy pattern is particularly well-suited for payment processing because:

1. **Flexibility**: Different payment methods can be added without modifying existing code
2. **Runtime Switching**: Payment methods can be changed at runtime
3. **Encapsulation**: Each payment method's logic is encapsulated in its own class
4. **Maintainability**: Easy to maintain and test individual payment strategies
5. **Open/Closed Principle**: New payment methods can be added without modifying existing code

## Adding New Payment Methods

To add a new payment method:

1. Create a new class that implements the `PaymentStrategy` interface
2. Implement the required methods: `process_payment` and `refund_payment`
3. Use the new strategy with the `PaymentGateway` class

Example:
```python
class NewPaymentStrategy(PaymentStrategy):
    def process_payment(self, amount: Decimal, currency: str, **kwargs) -> PaymentResult:
        # Implement payment processing logic
        pass
    
    def refund_payment(self, transaction_id: str, amount: Decimal, **kwargs) -> PaymentResult:
        # Implement refund processing logic
        pass
``` 