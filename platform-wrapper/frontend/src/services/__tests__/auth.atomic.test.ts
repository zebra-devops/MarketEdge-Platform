/**
 * US-AUTH-3: Unit tests for Atomic Auth State Transaction Pattern
 * Tests validate race condition prevention and rollback mechanisms
 */

import { authService } from '../auth'
import { User } from '@/types/auth'

// Mock window and document for JSDOM
Object.defineProperty(window, 'location', {
  writable: true,
  value: {
    search: '',
    hostname: 'localhost',
    protocol: 'http:',
    href: 'http://localhost:3000',
    pathname: '/',
  },
})

Object.defineProperty(document, 'cookie', {
  writable: true,
  value: '',
})

// Mock dependencies
jest.mock('../api', () => ({
  apiService: {
    post: jest.fn(),
    get: jest.fn(),
  },
}))

jest.mock('js-cookie', () => ({
  default: {
    get: jest.fn(),
    remove: jest.fn(),
  },
  get: jest.fn(),
  remove: jest.fn(),
}))

describe('US-AUTH-3: Atomic Auth State', () => {
  const mockUser: User = {
    id: 'user-123',
    email: 'test@example.com',
    name: 'Test User',
    role: 'admin',
    is_active: true,
    organization_id: 'org-123',
  }

  const mockTokenResponse = {
    access_token: 'mock_access_token_abc123',
    refresh_token: 'mock_refresh_token_xyz789',
    token_type: 'Bearer',
    expires_in: 3600,
    user: mockUser,
    tenant: {
      id: 'org-123',
      name: 'Test Org',
      industry: 'Cinema',
      subscription_plan: 'enterprise',
    },
    permissions: ['manage:feature_flags', 'admin:market_edge'],
  }

  beforeEach(() => {
    // Clear all storage before each test
    localStorage.clear()
    sessionStorage.clear()
    jest.clearAllMocks()

    // Enable atomic auth for tests
    localStorage.setItem('za:feature:atomic_auth', 'true')
  })

  afterEach(() => {
    localStorage.clear()
    sessionStorage.clear()
  })

  describe('Happy Path: Complete Auth State Persistence', () => {
    it('should persist and retrieve complete auth state atomically', () => {
      // Arrange: Access private method via type casting
      const service = authService as any

      // Act: Store atomic auth state
      service.setAtomicAuthState(mockTokenResponse)

      // Assert: Verify sessionStorage has complete state
      const storedState = sessionStorage.getItem('za:auth:v2')
      expect(storedState).toBeTruthy()

      const parsedState = JSON.parse(storedState!)
      expect(parsedState).toMatchObject({
        version: '2.0',
        access_token: mockTokenResponse.access_token,
        refresh_token: mockTokenResponse.refresh_token,
        user: mockUser,
        tenant: mockTokenResponse.tenant,
        permissions: mockTokenResponse.permissions,
      })
      expect(parsedState.expires_at).toBeTruthy()
      expect(parsedState.persisted_at).toBeGreaterThan(0)

      // Assert: Retrieve auth state
      const retrievedState = service.getAtomicAuthState()
      expect(retrievedState).toBeTruthy()
      expect(retrievedState.version).toBe('2.0')
      expect(retrievedState.access_token).toBe(mockTokenResponse.access_token)
      expect(retrievedState.user.email).toBe(mockUser.email)
    })

    it('should retrieve token via getToken() when atomic auth enabled', () => {
      // Arrange
      const service = authService as any
      service.setAtomicAuthState(mockTokenResponse)

      // Act
      const token = authService.getToken()

      // Assert
      expect(token).toBe(mockTokenResponse.access_token)
    })

    it('should retrieve user via getStoredUser() when atomic auth enabled', () => {
      // Arrange
      const service = authService as any
      service.setAtomicAuthState(mockTokenResponse)

      // Act
      const user = authService.getStoredUser()

      // Assert
      expect(user).toBeTruthy()
      expect(user?.email).toBe(mockUser.email)
      expect(user?.role).toBe(mockUser.role)
    })
  })

  describe('Input Validation', () => {
    it('should reject empty access token', () => {
      // Arrange
      const service = authService as any
      const invalidResponse = {
        ...mockTokenResponse,
        access_token: '',
      }

      // Act & Assert
      expect(() => {
        service.setAtomicAuthState(invalidResponse)
      }).toThrow('Invalid access token - cannot be empty')
    })

    it('should reject empty refresh token', () => {
      // Arrange
      const service = authService as any
      const invalidResponse = {
        ...mockTokenResponse,
        refresh_token: '',
      }

      // Act & Assert
      expect(() => {
        service.setAtomicAuthState(invalidResponse)
      }).toThrow('Invalid refresh token - cannot be empty')
    })

    it('should reject missing user data', () => {
      // Arrange
      const service = authService as any
      const invalidResponse = {
        ...mockTokenResponse,
        user: { email: '' } as any,
      }

      // Act & Assert
      expect(() => {
        service.setAtomicAuthState(invalidResponse)
      }).toThrow('Invalid user data - email required')
    })
  })

  describe('Rollback on Storage Failure', () => {
    it('should rollback on QuotaExceededError', () => {
      // Arrange: Mock sessionStorage to throw QuotaExceededError
      const service = authService as any
      const originalSetItem = Storage.prototype.setItem
      const quotaError = new Error('QuotaExceededError')
      quotaError.name = 'QuotaExceededError'

      Storage.prototype.setItem = jest.fn(() => {
        throw quotaError
      })

      // Act & Assert
      expect(() => {
        service.setAtomicAuthState(mockTokenResponse)
      }).toThrow('Browser storage quota exceeded - please clear browser data')

      // Assert: Verify no partial state left behind
      expect(sessionStorage.getItem('za:auth:v2')).toBeNull()
      expect(localStorage.getItem('za:auth:v2')).toBeNull()

      // Cleanup
      Storage.prototype.setItem = originalSetItem
    })

    it('should rollback on verification failure', () => {
      // Arrange: Mock to simulate verification failure
      const service = authService as any
      const originalGetItem = Storage.prototype.getItem
      let callCount = 0

      Storage.prototype.getItem = jest.fn((key: string) => {
        callCount++
        // First call (setItem verification) returns wrong value
        if (callCount === 1 && key === 'za:auth:v2') {
          return 'wrong_value'
        }
        return null
      })

      // Act & Assert
      expect(() => {
        service.setAtomicAuthState(mockTokenResponse)
      }).toThrow('Session storage verification failed')

      // Cleanup
      Storage.prototype.getItem = originalGetItem
    })
  })

  describe('Expiry Handling', () => {
    it('should reject expired auth state', () => {
      // Arrange: Create auth state with past expiry
      const service = authService as any
      const expiredState = {
        version: '2.0',
        access_token: 'expired_token',
        refresh_token: 'expired_refresh',
        user: mockUser,
        tenant: mockTokenResponse.tenant,
        permissions: mockTokenResponse.permissions,
        expires_at: new Date(Date.now() - 1000).toISOString(), // Expired 1 second ago
        persisted_at: Date.now() - 5000,
      }

      sessionStorage.setItem('za:auth:v2', JSON.stringify(expiredState))

      // Act
      const retrievedState = service.getAtomicAuthState()

      // Assert
      expect(retrievedState).toBeNull()
      // Verify rollback cleared the expired state
      expect(sessionStorage.getItem('za:auth:v2')).toBeNull()
    })

    it('should accept non-expired auth state', () => {
      // Arrange
      const service = authService as any
      const validState = {
        version: '2.0',
        access_token: 'valid_token',
        refresh_token: 'valid_refresh',
        user: mockUser,
        tenant: mockTokenResponse.tenant,
        permissions: mockTokenResponse.permissions,
        expires_at: new Date(Date.now() + 3600000).toISOString(), // Expires in 1 hour
        persisted_at: Date.now(),
      }

      sessionStorage.setItem('za:auth:v2', JSON.stringify(validState))

      // Act
      const retrievedState = service.getAtomicAuthState()

      // Assert
      expect(retrievedState).toBeTruthy()
      expect(retrievedState.access_token).toBe('valid_token')
    })
  })

  describe('Schema Version Validation', () => {
    it('should reject auth state with wrong schema version', () => {
      // Arrange
      const service = authService as any
      const wrongVersionState = {
        version: '1.0', // Wrong version
        access_token: 'token',
        refresh_token: 'refresh',
        user: mockUser,
      }

      sessionStorage.setItem('za:auth:v2', JSON.stringify(wrongVersionState))

      // Act
      const retrievedState = service.getAtomicAuthState()

      // Assert
      expect(retrievedState).toBeNull()
      // Verify rollback cleared the incompatible state
      expect(sessionStorage.getItem('za:auth:v2')).toBeNull()
    })
  })

  describe('Feature Flag Control', () => {
    it('should use atomic auth when URL parameter is set', () => {
      // Arrange: Mock window.location.search
      Object.defineProperty(window, 'location', {
        writable: true,
        value: {
          search: '?atomicAuth=1',
          hostname: 'localhost',
          protocol: 'http:',
        },
      })

      const service = authService as any

      // Act
      const shouldUse = service.useAtomicAuth()

      // Assert
      expect(shouldUse).toBe(true)

      // Cleanup
      Object.defineProperty(window, 'location', {
        writable: true,
        value: {
          search: '',
          hostname: 'localhost',
          protocol: 'http:',
        },
      })
    })

    it('should use atomic auth when localStorage setting is true', () => {
      // Arrange
      localStorage.setItem('za:feature:atomic_auth', 'true')
      Object.defineProperty(window, 'location', {
        writable: true,
        value: {
          search: '',
          hostname: 'localhost',
          protocol: 'http:',
        },
      })

      const service = authService as any

      // Act
      const shouldUse = service.useAtomicAuth()

      // Assert
      expect(shouldUse).toBe(true)
    })

    it('should default to false when no override is set', () => {
      // Arrange
      localStorage.removeItem('za:feature:atomic_auth')
      Object.defineProperty(window, 'location', {
        writable: true,
        value: {
          search: '',
          hostname: 'localhost',
          protocol: 'http:',
        },
      })

      const service = authService as any

      // Act
      const shouldUse = service.useAtomicAuth()

      // Assert
      expect(shouldUse).toBe(false)
    })
  })

  describe('Legacy Migration', () => {
    it('should clear legacy storage keys on migration', () => {
      // Arrange
      localStorage.setItem('za:feature:atomic_auth', 'true')
      localStorage.setItem('access_token', 'old_token')
      localStorage.setItem('refresh_token', 'old_refresh')
      localStorage.setItem('token_expires_at', new Date().toISOString())
      sessionStorage.setItem('auth_session_backup', '{}')

      const service = authService as any

      // Act
      service.migrateFromLegacyAuth()

      // Assert
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
      expect(localStorage.getItem('token_expires_at')).toBeNull()
      expect(sessionStorage.getItem('auth_session_backup')).toBeNull()
      expect(localStorage.getItem('za:auth:migrated')).toBe('true')
    })

    it('should only run migration once', () => {
      // Arrange
      localStorage.setItem('za:feature:atomic_auth', 'true')
      localStorage.setItem('za:auth:migrated', 'true')
      localStorage.setItem('access_token', 'old_token')

      const service = authService as any

      // Act
      service.migrateFromLegacyAuth()

      // Assert: Migration should not run again
      expect(localStorage.getItem('access_token')).toBe('old_token')
    })
  })

  describe('Rollback Mechanism', () => {
    it('should clear all atomic auth state on rollback', () => {
      // Arrange
      const service = authService as any
      service.setAtomicAuthState(mockTokenResponse)

      // Verify state exists
      expect(sessionStorage.getItem('za:auth:v2')).toBeTruthy()

      // Act
      service.rollbackAtomicAuthState()

      // Assert
      expect(sessionStorage.getItem('za:auth:v2')).toBeNull()
      expect(localStorage.getItem('za:auth:v2')).toBeNull()
      expect(service.temporaryAccessToken).toBeNull()
    })
  })
})
