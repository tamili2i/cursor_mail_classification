class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
    this.severity = 'warning';
  }
}

class PaymentError extends Error {
  constructor(message) {
    super(message);
    this.name = 'PaymentError';
    this.severity = 'critical';
  }
}

// Simple error logger (replace with real logger in production)
function logError(error, context = {}) {
  // Only log non-user errors or critical issues
  if (error.severity === 'critical' || error.severity === 'warning') {
    console.error(`[${new Date().toISOString()}] [${error.name}]`, error.message, context);
  }
}

function validateCartItems(cartItems) {
  if (cartItems == null) {
    throw new ValidationError('Cart items are required');
  }
  if (!Array.isArray(cartItems) || cartItems.length === 0) {
    throw new ValidationError('Cart is empty');
  }
  cartItems.forEach((item, i) => {
    if (typeof item !== 'object' || item == null) {
      throw new ValidationError(`Cart item at index ${i} is not an object`);
    }
    if (typeof item.price !== 'number' || isNaN(item.price) || item.price < 0) {
      throw new ValidationError(`Invalid price for cart item at index ${i}`);
    }
    if (typeof item.quantity !== 'number' || !Number.isInteger(item.quantity) || item.quantity <= 0) {
      throw new ValidationError(`Invalid quantity for cart item at index ${i}`);
    }
  });
}

function getDiscountValue(discountCode, total) {
  if (discountCode == null) return 0;
  if (typeof discountCode === 'number') {
    if (isNaN(discountCode) || discountCode <= 0 || discountCode >= total) {
      return 0;
    }
    return discountCode;
  }
  // If discountCode is a string, you could look it up in a table here
  // For now, only allow numeric discounts
  return 0;
}

function processPayment(total, cardNumber) {
  // Dummy implementation for demonstration
  if (!cardNumber || typeof cardNumber !== 'string' || cardNumber.length < 12) {
    throw new PaymentError('Invalid card number');
  }
  if (total === 0) {
    return { success: true, message: 'No payment needed' };
  }
  // Simulate payment success
  return { success: true, transactionId: 'TXN' + Date.now() };
}

function processCheckout(cartItems, userInfo, paymentData) {
  try {
    // Defensive: Validate all inputs early
    validateCartItems(cartItems);
    if (!userInfo || typeof userInfo !== 'object') {
      throw new ValidationError('User info is required');
    }
    if (!paymentData || typeof paymentData !== 'object') {
      throw new ValidationError('Payment data is required');
    }
    let total = 0;
    cartItems.forEach(item => {
      total += item.price * item.quantity;
    });
    // Apply discount
    let discount = 0;
    if (userInfo.discountCode) {
      discount = getDiscountValue(userInfo.discountCode, total);
      total -= discount;
    }
    // Defensive: prevent negative totals
    total = Math.max(0, total);
    // Process payment
    let paymentResult;
    try {
      paymentResult = processPayment(total, paymentData.cardNumber);
      if (!paymentResult || paymentResult.success === false) {
        throw new PaymentError('Payment failed');
      }
    } catch (err) {
      logError(err, { userInfo, total });
      // Graceful degradation: allow retry or alternative payment in real app
      return { error: 'Payment processing failed', details: err.message };
    }
    // Create order (do not expose sensitive user data)
    const order = {
      items: cartItems,
      total: total,
      discount: discount,
      paymentStatus: paymentResult.success ? 'success' : 'failed',
      timestamp: new Date(),
      transactionId: paymentResult.transactionId || null
    };
    return order;
  } catch (err) {
    logError(err, { cartItems, userInfo });
    // User-friendly error message
    return { error: err instanceof ValidationError ? err.message : 'An unexpected error occurred. Please try again.' };
  }
}