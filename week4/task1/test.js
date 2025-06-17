/**
 * Processes an array of user data and returns filtered premium active users
 * @param {Array} data - Array of user objects
 * @returns {Array} Array of processed user objects
 * @throws {Error} If input is invalid
 */
function processData(data) {
  // Input validation
  if (!Array.isArray(data)) {
    throw new Error('Input must be an array');
  }

  return data
    .filter(user => user != null)
    .filter(user => user.active === true)
    .filter(user => user.type === 'premium')
    .map(user => ({
      id: user.id,
      name: `${user.firstName} ${user.lastName}`,
      email: user.email,
      status: 'active'
    }));
}