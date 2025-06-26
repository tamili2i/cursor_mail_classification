function problematicFunction(data) {
  // AI suggested: Use feature flags for safe debugging
  if (isFeatureFlagEnabled('debug-mode') && isUserInDebugGroup()) {

  console.log('DEBUG: Input data:', JSON.stringify(data))
  console.log('DEBUG: Processing started at:', new Date().toISOString());
  }
  try {
  const result = processData(data);
  if (isFeatureFlagEnabled('debug-mode') &&
  isUserInDebugGroup()) {
  console.log('DEBUG: Processing completed:'
  , result);
  }
  return result;
  } catch (error) {
  // Enhanced error logging for debugging
  logger.error('Production error in problematicFunction'
  , {
  error: error.message,
  stack: error.stack,
  inputData: sanitizeForLogging(data),
  timestamp: new Date().toISOString(),
  userAgent: req?.headers['user-agent'],
  userId: req?.user?.id
  });
  throw error;
  }
  }