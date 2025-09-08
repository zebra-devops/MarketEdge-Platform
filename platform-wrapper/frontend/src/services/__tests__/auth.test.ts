/**
 * Enhanced Authentication Service Tests
 * Comprehensive tests for multi-tenant auth with permissions, token refresh, and session management
 */

import { AuthService, authService } from '../auth'
import { LoginRequest } from '@/types/auth'
import { apiService } from '../api'

// Mock dependencies
jest.mock('../api')
const mockApiService = apiService as jest.Mocked<typeof apiService>

// Mock js-cookie
const mockCookies = {
  set: jest.fn(),
  get: jest.fn(),
  remove: jest.fn(),
}
jest.mock('js-cookie', () => mockCookies)

// Mock localStorage
const mockLocalStorage = {
  store: {} as Record<string, string>,
  getItem: jest.fn((key: string) => mockLocalStorage.store[key] || null),
  setItem: jest.fn((key: string, value: string) => {
    mockLocalStorage.store[key] = value
  }),
  removeItem: jest.fn((key: string) => {
    delete mockLocalStorage.store[key]
  }),
  clear: jest.fn(() => {
    mockLocalStorage.store = {}
  })
}

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
})

// Mock window.location for logout redirect
const mockLocation = { href: '' }
Object.defineProperty(window, 'location', { value: mockLocation, writable: true })

describe('AuthService', () => {
  let service: AuthService

  beforeEach(() => {
    service = new AuthService()
    jest.clearAllMocks()
    mockLocation.href = ''
    mockLocalStorage.clear()
    
    // Reset mock implementations
    mockCookies.get.mockReturnValue(undefined)
    mockCookies.set.mockReturnValue(undefined)
    mockCookies.remove.mockReturnValue(undefined)
  })

  describe('login', () => {
    const validLoginRequest: LoginRequest = {
      code: 'valid-auth-code',
      redirect_uri: 'http://localhost:3000/callback',
    }

    it('should successfully login and set cookies', async () => {
      const result = await service.login(validLoginRequest)

      expect(mockCookies.set).toHaveBeenCalledWith('access_token', 'mock-jwt-token', { expires: 1 })
      expect(mockCookies.set).toHaveBeenCalledWith('refresh_token', 'mock-refresh-token', { expires: 7 })
      expect(result.access_token).toBe('mock-jwt-token')
    })

    it('should reject with invalid credentials', async () => {
      const invalidRequest: LoginRequest = {
        code: 'invalid-code', 
        redirect_uri: 'http://localhost:3000/callback',
      }

      await expect(service.login(invalidRequest)).rejects.toThrow()
    })
  })

  describe('getCurrentUser', () => {
    it('should fetch user when authenticated', async () => {
      mockCookies.get.mockImplementation((name) => name === 'access_token' ? 'valid-token' : undefined)

      const user = await service.getCurrentUser()

      expect(user.id).toBe('test-user-456')
      expect(user.email).toBe('test@example.com')
    })

    it('should handle unauthenticated request', async () => {
      mockCookies.get.mockReturnValue(undefined)

      await expect(service.getCurrentUser()).rejects.toThrow()
    })
  })

  describe('getAuth0Url', () => {
    it('should return Auth0 authorization URL', async () => {
      const redirectUri = 'http://localhost:3000/callback'
      
      const result = await service.getAuth0Url(redirectUri)
      
      expect(result.auth_url).toContain('auth0.com/authorize')
      expect(result.auth_url).toContain(encodeURIComponent(redirectUri))
    })

    it('should handle special characters in redirect URI', async () => {
      const specialUri = 'http://localhost:3000/callback?test=value&other=123'
      
      const result = await service.getAuth0Url(specialUri)
      
      expect(result.auth_url).toContain(encodeURIComponent(specialUri))
    })
  })

  describe('logout', () => {
    it('should remove cookies and redirect', () => {
      service.logout()

      expect(mockCookies.remove).toHaveBeenCalledWith('access_token')
      expect(mockCookies.remove).toHaveBeenCalledWith('refresh_token')
      expect(mockLocation.href).toBe('/login')
    })
  })

  describe('getToken', () => {
    it('should return token when exists', () => {
      mockCookies.get.mockReturnValue('test-token')

      const token = service.getToken()

      expect(mockCookies.get).toHaveBeenCalledWith('access_token')
      expect(token).toBe('test-token')
    })

    it('should return undefined when no token', () => {
      mockCookies.get.mockReturnValue(undefined)

      const token = service.getToken()

      expect(token).toBeUndefined()
    })

    it('should return empty string', () => {
      mockCookies.get.mockReturnValue('')

      const token = service.getToken()

      expect(token).toBe('')
    })
  })

  describe('isAuthenticated', () => {
    it('should return true when token exists', () => {
      mockCookies.get.mockReturnValue('valid-token')

      expect(service.isAuthenticated()).toBe(true)
    })

    it('should return false when no token', () => {
      mockCookies.get.mockReturnValue(undefined)

      expect(service.isAuthenticated()).toBe(false)
    })

    it('should return false for empty token', () => {
      mockCookies.get.mockReturnValue('')

      expect(service.isAuthenticated()).toBe(false)
    })

    it('should return false for null token', () => {
      mockCookies.get.mockReturnValue(null)

      expect(service.isAuthenticated()).toBe(false)
    })
  })

  describe('Multi-tenant scenarios', () => {
    it('should handle different tenant login codes', async () => {
      const hotelLogin: LoginRequest = {
        code: 'test-auth-code',
        redirect_uri: 'http://hotel.platform.com/callback',
      }

      const result = await service.login(hotelLogin)

      expect(result.user.organisation_id).toBe('test-tenant-123')
    })

    it('should maintain tenant context in token', () => {
      mockCookies.get.mockReturnValue('tenant-specific-token')

      const token = service.getToken()
      expect(token).toBe('tenant-specific-token')
    })
  })

  describe('Error handling', () => {
    it('should handle cookie errors gracefully', () => {
      mockCookies.get.mockImplementation(() => { throw new Error('Cookie error') })

      expect(() => service.getToken()).toThrow('Cookie error')
      expect(() => service.isAuthenticated()).toThrow('Cookie error')
    })

    it('should still logout even if cookie removal fails', () => {
      mockCookies.remove.mockImplementation(() => { throw new Error('Remove failed') })

      expect(() => service.logout()).not.toThrow()
      expect(mockLocation.href).toBe('/login')
    })
  })

  // Enhanced Authentication Tests
  describe('Enhanced Authentication Features', () => {
    describe('refreshToken', () => {
      it('should refresh token successfully', async () => {
        const mockRefreshToken = 'mock_refresh_token'
        mockCookies.get.mockImplementation((key) => {
          if (key === 'refresh_token') return mockRefreshToken
          return undefined
        })

        const mockResponse = {
          access_token: 'new_access_token',
          refresh_token: 'new_refresh_token',
          token_type: 'bearer',
          expires_in: 3600,
          user: {
            id: 'user123',
            email: 'test@example.com',
            role: 'admin',
            organisation_id: 'org456'
          },
          tenant: {
            id: 'org456',
            name: 'Test Organization',
            industry: 'Technology',
            subscription_plan: 'basic'
          },
          permissions: ['read:users']
        }

        mockApiService.post.mockResolvedValue(mockResponse)

        const result = await service.refreshToken()

        expect(mockApiService.post).toHaveBeenCalledWith('/auth/refresh', {
          refresh_token: mockRefreshToken
        })
        expect(result).toEqual(mockResponse)
      })

      it('should handle missing refresh token', async () => {
        mockCookies.get.mockReturnValue(undefined)

        await expect(service.refreshToken()).rejects.toThrow('No refresh token available')
      })
    })

    describe('permission management', () => {
      beforeEach(() => {
        const permissions = ['read:users', 'write:users', 'read:organizations']
        mockLocalStorage.setItem('user_permissions', JSON.stringify(permissions))
      })

      it('should check single permission correctly', () => {
        expect(service.hasPermission('read:users')).toBe(true)
        expect(service.hasPermission('delete:users')).toBe(false)
      })

      it('should check multiple permissions correctly', () => {
        expect(service.hasAnyPermission(['read:users', 'admin:all'])).toBe(true)
        expect(service.hasAnyPermission(['delete:users', 'admin:all'])).toBe(false)
      })

      it('should handle missing permissions gracefully', () => {
        mockLocalStorage.removeItem('user_permissions')
        
        expect(service.hasPermission('read:users')).toBe(false)
        expect(service.hasAnyPermission(['read:users'])).toBe(false)
      })
    })

    describe('tenant information', () => {
      it('should return tenant info when available', () => {
        const tenantInfo = {
          id: 'org456',
          name: 'Test Organization',
          industry: 'Technology',
          subscription_plan: 'basic'
        }

        mockLocalStorage.setItem('tenant_info', JSON.stringify(tenantInfo))

        const result = service.getTenantInfo()

        expect(result).toEqual(tenantInfo)
      })

      it('should return null when no tenant info exists', () => {
        const result = service.getTenantInfo()

        expect(result).toBeNull()
      })

      it('should handle corrupted tenant data gracefully', () => {
        mockLocalStorage.setItem('tenant_info', 'invalid json')

        const result = service.getTenantInfo()

        expect(result).toBeNull()
      })
    })

    describe('token refresh logic', () => {
      it('should determine when token needs refresh', () => {
        // Set token expiry to 2 minutes from now
        const expiryTime = new Date(Date.now() + 2 * 60 * 1000)
        mockLocalStorage.setItem('token_expires_at', expiryTime.toISOString())

        // Should need refresh (within 5 minute threshold)
        expect(service.shouldRefreshToken()).toBe(true)
      })

      it('should not refresh when token has plenty of time left', () => {
        // Set token expiry to 10 minutes from now
        const expiryTime = new Date(Date.now() + 10 * 60 * 1000)
        mockLocalStorage.setItem('token_expires_at', expiryTime.toISOString())

        // Should not need refresh
        expect(service.shouldRefreshToken()).toBe(false)
      })

      it('should handle missing expiry time', () => {
        mockLocalStorage.removeItem('token_expires_at')
        
        expect(service.shouldRefreshToken()).toBe(false)
      })
    })

    describe('ensureValidToken', () => {
      it('should return token if valid and not expiring soon', async () => {
        const mockToken = 'valid_token'
        mockCookies.get.mockReturnValue(mockToken)
        
        // Set expiry far in future
        const expiryTime = new Date(Date.now() + 30 * 60 * 1000)
        mockLocalStorage.setItem('token_expires_at', expiryTime.toISOString())

        const result = await service.ensureValidToken()

        expect(result).toBe(mockToken)
      })

      it('should refresh token if expiring soon', async () => {
        const oldToken = 'old_token'
        const newToken = 'new_token'
        
        mockCookies.get
          .mockReturnValueOnce(oldToken) // First call returns old token
          .mockReturnValue(newToken) // Subsequent calls return new token

        // Set expiry to 2 minutes from now (within refresh threshold)
        const expiryTime = new Date(Date.now() + 2 * 60 * 1000)
        mockLocalStorage.setItem('token_expires_at', expiryTime.toISOString())

        const mockRefreshResponse = {
          access_token: newToken,
          refresh_token: 'new_refresh',
          expires_in: 3600,
          user: { id: 'user123' },
          tenant: { id: 'org456' },
          permissions: []
        }

        mockApiService.post.mockResolvedValue(mockRefreshResponse)

        const result = await service.ensureValidToken()

        expect(mockApiService.post).toHaveBeenCalledWith('/auth/refresh', expect.any(Object))
        expect(result).toBe(newToken)
      })
    })

    describe('enhanced logout', () => {
      it('should logout with server-side token revocation', async () => {
        const mockRefreshToken = 'refresh_token'
        mockCookies.get.mockReturnValue(mockRefreshToken)
        mockApiService.post.mockResolvedValue({ message: 'Logout successful' })

        await service.logout(false)

        expect(mockApiService.post).toHaveBeenCalledWith('/auth/logout', {
          refresh_token: mockRefreshToken,
          all_devices: false
        })

        // Check that data was cleared
        expect(mockCookies.remove).toHaveBeenCalledWith('access_token')
        expect(mockCookies.remove).toHaveBeenCalledWith('refresh_token')
        expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('current_user')
        expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('tenant_info')
        expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('user_permissions')
        expect(mockLocation.href).toBe('/login')
      })
    })

    describe('session management', () => {
      it('should check session successfully', async () => {
        const mockResponse = {
          authenticated: true,
          user_id: 'user123',
          tenant_id: 'org456',
          role: 'admin',
          active: true
        }

        mockApiService.get.mockResolvedValue(mockResponse)

        const result = await service.checkSession()

        expect(mockApiService.get).toHaveBeenCalledWith('/auth/session/check')
        expect(result).toEqual(mockResponse)
      })

      it('should extend session when needed', async () => {
        const mockResponse = {
          extend_recommended: true,
          message: 'Token should be refreshed',
          expires_soon: true
        }

        mockApiService.post.mockResolvedValue(mockResponse)

        const result = await service.extendSession()

        expect(mockApiService.post).toHaveBeenCalledWith('/auth/session/extend')
        expect(result).toEqual(mockResponse)
      })
    })

    describe('enhanced authentication state', () => {
      it('should return true for authenticated when token and user exist', () => {
        mockCookies.get.mockReturnValue('access_token')
        mockLocalStorage.setItem('current_user', JSON.stringify({ id: 'user123' }))

        expect(service.isAuthenticated()).toBe(true)
      })

      it('should return false when no token exists', () => {
        mockCookies.get.mockReturnValue(undefined)
        mockLocalStorage.setItem('current_user', JSON.stringify({ id: 'user123' }))

        expect(service.isAuthenticated()).toBe(false)
      })

      it('should return false when no user data exists', () => {
        mockCookies.get.mockReturnValue('access_token')
        mockLocalStorage.removeItem('current_user')

        expect(service.isAuthenticated()).toBe(false)
      })
    })
  })
})

describe('Singleton authService', () => {
  it('should export singleton instance', () => {
    expect(authService).toBeInstanceOf(AuthService)
  })

  it('should maintain same instance', () => {
    expect(authService).toBe(authService)
  })
})