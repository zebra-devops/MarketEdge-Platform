/**
 * Global Jest setup for multi-tenant testing environment
 * Runs once before all test suites
 */

module.exports = async () => {
  // Set test environment variables
  process.env.NODE_ENV = 'test'
  process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000/api/v1'
  process.env.NEXT_PUBLIC_APP_ENV = 'test'
  
  // Mock Auth0 configuration for testing
  process.env.AUTH0_DOMAIN = 'test.auth0.com'
  process.env.AUTH0_CLIENT_ID = 'test_client_id'
  process.env.AUTH0_CLIENT_SECRET = 'test_client_secret'
  
  // Console log to indicate test environment setup
  console.log('🧪 Jest Global Setup: Test environment initialized')
  
  // Setup any global test data or services needed across all tests
  global.__TEST_CONFIG__ = {
    api: {
      baseUrl: 'http://localhost:8000/api/v1',
      timeout: 5000,
    },
    tenant: {
      defaultTenantId: 'test-tenant-id',
      testTenants: [
        {
          id: 'cinema-tenant',
          name: 'Cinema Corp',
          industry: 'cinema',
        },
        {
          id: 'hotel-tenant', 
          name: 'Hotel Group',
          industry: 'hotel',
        },
        {
          id: 'gym-tenant',
          name: 'Fitness Chain',
          industry: 'gym',
        },
      ],
    },
    users: {
      admin: {
        id: 'admin-user-id',
        email: 'admin@test.com',
        role: 'admin',
        organisation_id: 'test-tenant-id',
      },
      user: {
        id: 'regular-user-id',
        email: 'user@test.com',
        role: 'user',
        organisation_id: 'test-tenant-id',
      },
    },
  }
  
  // Store original console methods to restore after tests
  global.__ORIGINAL_CONSOLE__ = {
    log: console.log,
    warn: console.warn,
    error: console.error,
    debug: console.debug,
  }
}