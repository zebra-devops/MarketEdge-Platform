/**
 * US-AUTH-3: E2E test for auth state persistence during navigation
 * Validates that atomic auth state prevents "ghost auth" during login flow interruptions
 */

import { test, expect } from '@playwright/test'

test.describe('US-AUTH-3: Auth State Persistence During Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Enable atomic auth feature via localStorage
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.setItem('za:feature:atomic_auth', 'true')
    })
  })

  test('should maintain auth state when navigating mid-login', async ({ page }) => {
    // Step 1: Start login flow with atomic auth enabled
    await page.goto('/?atomicAuth=1')

    // Mock Auth0 callback with valid authorization code
    const mockAuthCode = 'mock_auth_code_' + Date.now()
    const callbackUrl = `${page.url()}auth/callback?code=${mockAuthCode}&state=test_state`

    // Step 2: Intercept backend authentication request
    await page.route('**/api/v1/auth/login-oauth2', async (route) => {
      // Simulate successful authentication
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'test_access_token_abc123',
          refresh_token: 'test_refresh_token_xyz789',
          token_type: 'Bearer',
          expires_in: 3600,
          user: {
            id: 'user-123',
            email: 'test@example.com',
            name: 'Test User',
            role: 'admin',
            is_active: true,
            organization_id: 'org-123',
          },
          tenant: {
            id: 'org-123',
            name: 'Test Organization',
            industry: 'Cinema',
            subscription_plan: 'enterprise',
          },
          permissions: ['manage:feature_flags', 'admin:market_edge'],
        }),
      })
    })

    // Step 3: Navigate to callback page
    await page.goto(callbackUrl)

    // Step 4: CRITICAL TEST - Navigate away mid-login (simulate race condition)
    // This should NOT cause auth state loss with atomic auth enabled
    await page.waitForTimeout(100) // Simulate timing window for race condition

    // Navigate to dashboard before login fully completes
    await page.goto('/dashboard')

    // Step 5: Verify auth state persists
    const atomicAuthState = await page.evaluate(() => {
      const stateJson = sessionStorage.getItem('za:auth:v2')
      return stateJson ? JSON.parse(stateJson) : null
    })

    // Assert: Atomic auth state should be complete
    expect(atomicAuthState).toBeTruthy()
    expect(atomicAuthState.version).toBe('2.0')
    expect(atomicAuthState.access_token).toBeTruthy()
    expect(atomicAuthState.refresh_token).toBeTruthy()
    expect(atomicAuthState.user).toBeTruthy()
    expect(atomicAuthState.user.email).toBe('test@example.com')
    expect(atomicAuthState.tenant).toBeTruthy()
    expect(atomicAuthState.permissions).toBeTruthy()

    // Assert: No "ghost auth state" - both tokens and user data present
    const hasToken = await page.evaluate(() => {
      const authService = (window as any).authService
      return authService?.getToken() !== undefined
    })

    const hasUser = await page.evaluate(() => {
      const authService = (window as any).authService
      return authService?.getStoredUser() !== null
    })

    expect(hasToken).toBe(true)
    expect(hasUser).toBe(true)
  })

  test('should not create ghost auth state if navigation interrupts login', async ({ page }) => {
    // Step 1: Start login flow
    await page.goto('/?atomicAuth=1')

    // Step 2: Mock successful backend authentication
    await page.route('**/api/v1/auth/login-oauth2', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'test_token',
          refresh_token: 'test_refresh',
          token_type: 'Bearer',
          expires_in: 3600,
          user: {
            id: 'user-456',
            email: 'ghost@example.com',
            name: 'Ghost Test',
            role: 'user',
            is_active: true,
            organization_id: 'org-456',
          },
          tenant: {
            id: 'org-456',
            name: 'Ghost Org',
            industry: 'Hotel',
            subscription_plan: 'professional',
          },
          permissions: ['view:dashboards'],
        }),
      })
    })

    // Step 3: Navigate to callback and immediately navigate away
    const callbackUrl = `/auth/callback?code=test_code_${Date.now()}&state=test`
    await page.goto(callbackUrl)

    // Immediately navigate to another page
    await page.goto('/dashboard')

    // Step 4: Verify NO ghost auth state exists
    const tokenPresent = await page.evaluate(() => {
      const stateJson = sessionStorage.getItem('za:auth:v2')
      if (!stateJson) return false

      const state = JSON.parse(stateJson)
      return !!state.access_token
    })

    const userPresent = await page.evaluate(() => {
      const stateJson = sessionStorage.getItem('za:auth:v2')
      if (!stateJson) return false

      const state = JSON.parse(stateJson)
      return !!state.user
    })

    // Assert: Either both present (complete auth) or both absent (no auth)
    // Never token without user or user without token (ghost state)
    expect(tokenPresent === userPresent).toBe(true)
  })

  test('should handle quota exceeded error gracefully', async ({ page }) => {
    // Step 1: Navigate to login page
    await page.goto('/?atomicAuth=1')

    // Step 2: Mock sessionStorage.setItem to throw QuotaExceededError
    await page.evaluate(() => {
      const originalSetItem = Storage.prototype.setItem
      Storage.prototype.setItem = function (key: string, value: string) {
        if (key === 'za:auth:v2') {
          const error: any = new Error('QuotaExceededError')
          error.name = 'QuotaExceededError'
          throw error
        }
        return originalSetItem.call(this, key, value)
      }
    })

    // Step 3: Attempt login - should show quota error
    await page.route('**/api/v1/auth/login-oauth2', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'test_token',
          refresh_token: 'test_refresh',
          token_type: 'Bearer',
          expires_in: 3600,
          user: {
            id: 'user-789',
            email: 'quota@example.com',
            name: 'Quota Test',
            role: 'user',
            is_active: true,
            organization_id: 'org-789',
          },
          tenant: {
            id: 'org-789',
            name: 'Quota Org',
            industry: 'Retail',
            subscription_plan: 'starter',
          },
          permissions: [],
        }),
      })
    })

    const callbackUrl = `/auth/callback?code=quota_test_${Date.now()}&state=test`
    await page.goto(callbackUrl)

    // Step 4: Verify error handling
    // Should not have partial auth state
    const hasPartialState = await page.evaluate(() => {
      return sessionStorage.getItem('za:auth:v2') !== null
    })

    expect(hasPartialState).toBe(false)
  })

  test('should reject expired auth state on retrieval', async ({ page }) => {
    // Step 1: Manually set expired auth state in sessionStorage
    await page.goto('/?atomicAuth=1')

    await page.evaluate(() => {
      const expiredState = {
        version: '2.0',
        access_token: 'expired_token',
        refresh_token: 'expired_refresh',
        user: {
          id: 'user-999',
          email: 'expired@example.com',
          name: 'Expired User',
          role: 'user',
          is_active: true,
          organization_id: 'org-999',
        },
        tenant: {
          id: 'org-999',
          name: 'Expired Org',
          industry: 'Gym',
          subscription_plan: 'basic',
        },
        permissions: [],
        expires_at: new Date(Date.now() - 1000).toISOString(), // Expired 1 second ago
        persisted_at: Date.now() - 5000,
      }

      sessionStorage.setItem('za:auth:v2', JSON.stringify(expiredState))
    })

    // Step 2: Try to retrieve auth state
    const retrievedState = await page.evaluate(() => {
      const authService = (window as any).authService
      return authService?.getAtomicAuthState?.()
    })

    // Assert: Should be null (expired state rejected and cleared)
    expect(retrievedState).toBeNull()

    // Assert: Expired state should be rolled back
    const stateAfterRollback = await page.evaluate(() => {
      return sessionStorage.getItem('za:auth:v2')
    })

    expect(stateAfterRollback).toBeNull()
  })

  test('should verify auth state with correct schema version', async ({ page }) => {
    // Step 1: Set auth state with wrong schema version
    await page.goto('/?atomicAuth=1')

    await page.evaluate(() => {
      const wrongVersionState = {
        version: '1.0', // Wrong version
        access_token: 'token',
        refresh_token: 'refresh',
        user: { email: 'test@example.com' },
        tenant: {},
        permissions: [],
        expires_at: new Date(Date.now() + 3600000).toISOString(),
        persisted_at: Date.now(),
      }

      sessionStorage.setItem('za:auth:v2', JSON.stringify(wrongVersionState))
    })

    // Step 2: Try to retrieve auth state
    const retrievedState = await page.evaluate(() => {
      const authService = (window as any).authService
      return authService?.getAtomicAuthState?.()
    })

    // Assert: Should be null (wrong version rejected)
    expect(retrievedState).toBeNull()

    // Assert: Wrong version state should be rolled back
    const stateAfterRollback = await page.evaluate(() => {
      return sessionStorage.getItem('za:auth:v2')
    })

    expect(stateAfterRollback).toBeNull()
  })
})
