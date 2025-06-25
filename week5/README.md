# Bug Hunting JS

## Overview

`bug-hunting.js` is a robust, production-ready JavaScript module for processing e-commerce checkouts with a strong focus on intelligent error handling. It demonstrates defensive programming, exception management, error monitoring, graceful degradation, and prevention strategies, making it suitable for real-world applications where reliability and user experience are critical.

## Error Handling Philosophy

This module is designed with the following error handling principles:

- **Defensive Programming:** Early validation and sanitization of all inputs, type and boundary checks, and prevention of invalid states.
- **Exception Management:** Use of custom error classes (`ValidationError`, `PaymentError`) for clarity, with try-catch blocks at logical boundaries and clear, user-friendly error messages.
- **Error Monitoring:** Centralized error logging with severity categorization. Critical and warning errors are logged with context for monitoring and alerting.
- **Graceful Degradation:** Fallbacks and defaults are used where possible. User-facing errors are clear and never expose sensitive information. Payment failures and validation errors are handled gracefully.
- **Prevention Strategies:** Guard clauses, early validation, and reliable code patterns prevent many common errors before they occur.

## Usage

1. **Import or include `bug-hunting.js` in your project.**
2. **Call `processCheckout(cartItems, userInfo, paymentData)`** with:
   - `cartItems`: Array of objects, each with `price` (number) and `quantity` (integer > 0).
   - `userInfo`: Object with optional `discountCode` (number or string).
   - `paymentData`: Object with `cardNumber` (string, at least 12 digits).

Example:
```js
const result = processCheckout(
  [ { price: 10, quantity: 2 } ],
  { discountCode: 5 },
  { cardNumber: '123456789012' }
);
console.log(result);
```

## Error Handling in Action
- Invalid inputs (e.g., empty cart, bad types, invalid card) return user-friendly error objects.
- Payment failures are logged and reported without exposing sensitive details.
- All critical and warning errors are logged with context for monitoring.

## Testing

- Test with valid and invalid cart items, user info, and payment data.
- Check that errors are logged and returned as expected.
- Extend `logError` to integrate with your preferred logging/monitoring service.

## Extending
- Replace the dummy `processPayment` with real payment gateway logic.
- Add more discount code logic in `getDiscountValue` as needed.
- Integrate with a real error monitoring service for production use.

---

**AI Driven Development #60day challenge**

This module is part of an AI-driven development challenge, focusing on reliability, maintainability, and production-readiness in error handling. 