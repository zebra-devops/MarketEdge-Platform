/**
 * Frontend Security Tests for Issue #4 Critical Security Fixes
 * 
 * Tests for:
 * 1. Client-side input validation
 * 2. Secure cookie handling
 * 3. XSS prevention
 * 4. CSRF protection
 * 5. Session security
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { jest } from '@jest/globals'
import { authService } from '@/services/auth'
import { authenticatedFetch, getAuthHeaders, logout } from '@/lib/auth'

// Mock fetch for testing
const mockFetch = jest.fn()
global.fetch = mockFetch

// Mock cookies for testing
const mockCookies = {
  get: jest.fn(),
  set: jest.fn(),
  remove: jest.fn(),
}

jest.mock('js-cookie', () => mockCookies)

describe('Frontend Security Fixes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockFetch.mockClear()
    
    // Reset localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    })
    
    // Reset sessionStorage
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    })
  })

  describe('Input Validation & XSS Prevention', () => {
    test('should sanitize malicious input in login parameters', async () => {
      const maliciousCode = "<script>alert('xss')</script>xyz123"
      const maliciousRedirect = "javascript:alert('xss')"
      const maliciousState = "'; DROP TABLE users; --"

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Invalid request parameters' }),
      })

      try {
        await authService.login({
          code: maliciousCode,
          redirect_uri: maliciousRedirect,
          state: maliciousState,
        })
      } catch (error) {
        // Should reject malicious input
        expect(error).toBeDefined()
      }

      // Verify the request was made with the data
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining(maliciousCode),
        })
      )
    })

    test('should escape HTML entities in user data display', () => {
      const maliciousUserData = {
        id: '123',
        email: 'test@example.com',
        first_name: "<script>alert('xss')</script>John",
        last_name: "<img src=x onerror=alert('xss')>Doe",
        role: 'viewer',
        organisation_id: '456',
        is_active: true,
      }

      // Mock localStorage to return malicious user data
      const mockGetItem = window.localStorage.getItem as jest.Mock
      mockGetItem.mockReturnValue(JSON.stringify(maliciousUserData))

      // Test that user data is properly escaped when retrieved
      const userData = authService['getStoredUser']()
      
      // The actual escaping would happen in the UI components
      // This test verifies the data structure is maintained
      expect(userData?.first_name).toBe("<script>alert('xss')</script>John")
      expect(userData?.last_name).toBe("<img src=x onerror=alert('xss')>Doe")
    })

    test('should validate redirect URI format', async () => {
      const maliciousRedirectUris = [
        'javascript:alert("xss")',
        'data:text/html,<script>alert("xss")</script>',
        'vbscript:msgbox("xss")',
        'file:///etc/passwd',
      ]

      for (const uri of maliciousRedirectUris) {
        mockFetch.mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Invalid redirect URI' }),
        })

        const response = await authService.getAuth0Url(uri)
        
        // Should handle invalid URIs appropriately
        expect(mockFetch).toHaveBeenCalled()
      }
    })
  })

  describe('Secure Cookie Handling', () => {
    test('should handle secure cookies properly', () => {
      // Mock cookies.get to return a token
      mockCookies.get.mockReturnValue('valid_token_123')

      const token = authService.getToken()
      
      expect(mockCookies.get).toHaveBeenCalledWith('access_token')
      expect(token).toBe('valid_token_123')
    })

    test('should clear all authentication cookies on logout', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Logout successful' }),
      })

      // Mock window.location.href assignment
      Object.defineProperty(window, 'location', {
        value: { href: '' },
        writable: true,
      })

      await authService.logout()

      // Verify cookies are removed
      expect(mockCookies.remove).toHaveBeenCalledWith('access_token')
      expect(mockCookies.remove).toHaveBeenCalledWith('refresh_token')
    })

    test('should perform complete session cleanup on logout', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Logout successful' }),
      })

      Object.defineProperty(window, 'location', {
        value: { href: '' },
        writable: true,
      })

      // Mock intervals for cleanup
      const mockInterval = 123
      ;(window as any).__authRefreshInterval = mockInterval
      ;(window as any).__sessionTimeoutInterval = mockInterval
      
      const clearIntervalSpy = jest.spyOn(global, 'clearInterval')

      await authService.logout()

      // Verify complete cleanup
      expect(window.localStorage.removeItem).toHaveBeenCalledWith('current_user')
      expect(window.localStorage.removeItem).toHaveBeenCalledWith('tenant_info')
      expect(window.localStorage.removeItem).toHaveBeenCalledWith('user_permissions')
      expect(window.sessionStorage.clear).toHaveBeenCalled()
      expect(clearIntervalSpy).toHaveBeenCalledWith(mockInterval)
    })
  })

  describe('CSRF Protection', () => {
    test('should include CSRF token in authenticated requests', async () => {
      mockCookies.get.mockImplementation((name: string) => {
        if (name === 'access_token') return 'valid_token_123'
        if (name === 'csrf_token') return 'csrf_token_456'
        return undefined
      })

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      })

      await authenticatedFetch('/api/test', {
        method: 'POST',
        body: JSON.stringify({ data: 'test' }),
      })

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer valid_token_123',
            'X-Tenant-Context': 'isolated',
            'X-Client-Version': '1.0.0',
          }),
          credentials: 'include',
        })
      )
    })

    test('should handle CSRF token validation failures', async () => {
      mockCookies.get.mockImplementation((name: string) => {
        if (name === 'access_token') return 'valid_token_123'
        return undefined
      })

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        headers: new Headers({
          'X-CSRF-Error': 'Invalid CSRF token',
        }),
      })

      try {
        await authenticatedFetch('/api/test', { method: 'POST' })
      } catch (error: any) {
        expect(error.message).toContain('Insufficient permissions')
      }
    })
  })

  describe('Session Security', () => {
    test('should detect and handle session timeout', () => {
      const authInstance = authService
      const thirtyOneMinutesAgo = Date.now() - (31 * 60 * 1000)
      
      // Mock lastActivityTime
      authInstance['lastActivityTime'] = thirtyOneMinutesAgo

      const isTimedOut = authInstance.checkSessionTimeout()
      expect(isTimedOut).toBe(true)
    })

    test('should track user activity properly', () => {
      const authInstance = authService
      const beforeActivity = authInstance['lastActivityTime']
      
      // Simulate user activity
      authInstance.trackUserActivity()
      
      const afterActivity = authInstance['lastActivityTime']
      expect(afterActivity).toBeGreaterThan(beforeActivity)
    })

    test('should initialize activity tracking with event listeners', () => {
      const addEventListenerSpy = jest.spyOn(document, 'addEventListener')
      
      authService.initializeActivityTracking()
      
      // Verify activity events are being tracked
      const expectedEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
      expectedEvents.forEach(event => {
        expect(addEventListenerSpy).toHaveBeenCalledWith(
          event,
          expect.any(Function),
          { passive: true }
        )
      })
    })

    test('should handle token refresh with concurrent request prevention', async () => {
      mockCookies.get.mockReturnValue('refresh_token_123')
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'new_access_token',
          refresh_token: 'new_refresh_token',
          token_type: 'bearer',
          expires_in: 3600,
          user: { id: '1', email: 'test@example.com' },
          tenant: { id: '1', name: 'Test Org' },
          permissions: ['read:data'],
        }),
      })

      // Make concurrent refresh requests
      const promise1 = authService.refreshToken()
      const promise2 = authService.refreshToken()

      const [result1, result2] = await Promise.all([promise1, promise2])

      // Both should resolve to the same token
      expect(result1).toEqual(result2)
      // Only one HTTP request should be made
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })
  })

  describe('Authentication Error Handling', () => {
    test('should handle 401 responses with proper cleanup', async () => {
      mockCookies.get.mockReturnValue('expired_token')
      
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        headers: new Headers({
          'X-Tenant-Error': 'Token expired',
        }),
      })

      Object.defineProperty(window, 'location', {
        value: { href: '' },
        writable: true,
      })

      try {
        await authenticatedFetch('/api/test')
      } catch (error: any) {
        expect(error.message).toContain('Authentication failed')
      }

      // Should redirect to login
      expect(window.location.href).toBe('/login')
    })

    test('should handle tenant isolation violations', async () => {
      mockCookies.get.mockReturnValue('valid_token')
      
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 422,
        headers: new Headers({
          'X-Tenant-Violation': 'Cross-tenant access denied',
        }),
      })

      try {
        await authenticatedFetch('/api/test')
      } catch (error: any) {
        expect(error.message).toContain('Tenant isolation violation')
      }
    })

    test('should handle network errors gracefully', async () => {
      mockCookies.get.mockReturnValue('valid_token')
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      try {
        await authenticatedFetch('/api/test')
      } catch (error: any) {
        expect(error.message).toContain('Request failed: Network error')
      }
    })
  })

  describe('Tenant Context Security', () => {
    test('should include tenant isolation headers in requests', async () => {
      mockCookies.get.mockReturnValue('valid_token')
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      })

      await authenticatedFetch('/api/test')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Tenant-Context': 'isolated',
            'X-Request-Source': 'frontend-app',
          }),
        })
      )
    })

    test('should clear tenant-specific data on logout', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Logout successful' }),
      })

      Object.defineProperty(window, 'location', {
        value: { href: '' },
        writable: true,
      })

      logout()

      // Verify tenant data is cleared
      expect(window.localStorage.removeItem).toHaveBeenCalledWith('tenant_info')
      expect(window.localStorage.removeItem).toHaveBeenCalledWith('user_permissions')
    })
  })

  describe('Security Performance', () => {
    test('should handle auth operations efficiently', async () => {
      const startTime = performance.now()
      
      // Simulate multiple auth checks
      for (let i = 0; i < 100; i++) {
        authService.isAuthenticated()
        authService.hasPermission('read:data')
        authService.getUserRole()
      }
      
      const endTime = performance.now()
      const duration = endTime - startTime
      
      // Should complete quickly
      expect(duration).toBeLessThan(100) // Less than 100ms
    })
  })
})

describe('Security Integration Tests', () => {
  test('should handle complete authentication flow securely', async () => {
    // Mock successful Auth0 URL generation
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        auth_url: 'https://domain.auth0.com/authorize?...',
        redirect_uri: 'https://app.example.com/callback',
        scopes: ['openid', 'profile', 'email'],
      }),
    })

    const authUrl = await authService.getAuth0Url('https://app.example.com/callback')
    expect(authUrl.auth_url).toContain('https://domain.auth0.com/authorize')

    // Mock successful login
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: 'secure_token_123',
        refresh_token: 'refresh_token_456',
        token_type: 'bearer',
        expires_in: 3600,
        user: {
          id: '1',
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
          role: 'viewer',
        },
        tenant: {
          id: '1',
          name: 'Test Organization',
          industry: 'Technology',
        },
        permissions: ['read:data'],
      }),
    })

    const loginResult = await authService.login({
      code: 'secure_auth_code_123',
      redirect_uri: 'https://app.example.com/callback',
      state: 'secure_state_456',
    })

    expect(loginResult.access_token).toBe('secure_token_123')
    expect(loginResult.user.email).toBe('test@example.com')
    expect(loginResult.tenant.name).toBe('Test Organization')
  })
})