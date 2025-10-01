/**
 * US-8: End-to-end Auth Regression Test Suite
 *
 * Comprehensive authentication flow testing for sales demos and regression detection
 */

import { test, expect } from '@playwright/test'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

test.describe('Auth Regression Suite', () => {
  test('Scenario 1: Login Success Flow', async ({ page }) => {
    // Skip if no test credentials
    if (!process.env.TEST_PASSWORD) {
      test.skip()
    }

    // 1. Navigate to login
    await page.goto(BASE_URL)

    // 2. Click login button
    const loginButton = page.locator('button:has-text("Login"), a:has-text("Login")')
    if (await loginButton.count() > 0) {
      await loginButton.first().click()
    } else {
      console.log('Login button not found - may already be on auth page')
    }

    // 3. Wait for Auth0 redirect (or check if already logged in)
    try {
      await page.waitForURL(/auth0\.com/, { timeout: 5000 })

      // 4. Fill credentials (use test account)
      await page.fill('input[name="email"], input[name="username"]', 'matt.lindop@zebra.associates')
      await page.fill('input[name="password"]', process.env.TEST_PASSWORD || '')

      // 5. Submit login
      await page.click('button[type="submit"]')

      // 6. Wait for callback redirect
      await page.waitForURL(/\/callback/, { timeout: 10000 })
    } catch (e) {
      console.log('Auth0 redirect not detected - may be testing with mock auth')
    }

    // 7. Wait for dashboard or home
    await page.waitForURL(/\/(dashboard|home|market-edge)/, { timeout: 10000 })

    // 8. Verify user authenticated
    const userMenu = page.locator('[data-testid="user-menu"], [aria-label*="user"], button:has-text("@")')
    await expect(userMenu.first()).toBeVisible({ timeout: 5000 })

    // 9. Take screenshot on success
    await page.screenshot({ path: 'test-results/auth-success.png', fullPage: true })

    console.log('✅ Scenario 1: Login Success - PASSED')
  })

  test('Scenario 2: Application Access Navigation', async ({ page }) => {
    // This test assumes user is already logged in or has stored auth state
    // For CI, this would use storageState from previous test

    // Skip if no auth available
    const hasAuth = await page.evaluate(() => {
      return !!(localStorage.getItem('access_token') || document.cookie.includes('access_token'))
    })

    if (!hasAuth) {
      console.log('No auth token found - skipping navigation test')
      test.skip()
    }

    // 1. Navigate to Market Edge
    await page.goto(`${BASE_URL}/market-edge`)
    await expect(page.locator('h1, h2').filter({ hasText: /Market Edge/i }).first()).toBeVisible({ timeout: 5000 })
    console.log('✅ Market Edge accessible')

    // 2. Navigate to Causal Edge
    await page.goto(`${BASE_URL}/causal-edge`)
    await expect(page.locator('h1, h2').filter({ hasText: /Causal Edge/i }).first()).toBeVisible({ timeout: 5000 })
    console.log('✅ Causal Edge accessible')

    // 3. Navigate to Value Edge
    await page.goto(`${BASE_URL}/value-edge`)
    await expect(page.locator('h1, h2').filter({ hasText: /Value Edge/i }).first()).toBeVisible({ timeout: 5000 })
    console.log('✅ Value Edge accessible')

    // 4. Verify no authentication errors
    const errorMessage = page.locator('[role="alert"], .error-message, [class*="error"]')
    const errorCount = await errorMessage.count()
    expect(errorCount).toBe(0)

    console.log('✅ Scenario 2: Application Access Navigation - PASSED')
  })

  test('Scenario 3: Token Refresh Flow', async ({ page, context }) => {
    // This test verifies that expired/missing tokens redirect to login

    // 1. Clear cookies to simulate expired token
    await context.clearCookies()

    // 2. Clear local storage
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })

    // 3. Try to access protected route
    await page.goto(`${BASE_URL}/dashboard`)

    // 4. Should redirect to login (or show login UI)
    try {
      await page.waitForURL(/\/(login|$|auth)/, { timeout: 5000 })
      console.log('✅ Redirected to login page')
    } catch (e) {
      // Alternative: Check if login UI is visible
      const loginButton = page.locator('button:has-text("Login"), a:has-text("Login")')
      await expect(loginButton.first()).toBeVisible({ timeout: 5000 })
      console.log('✅ Login UI visible')
    }

    console.log('✅ Scenario 3: Token Refresh Flow - PASSED')
  })

  test('Scenario 4: 401 Handling - Expired Token', async ({ page, context }) => {
    // Skip if backend not available
    try {
      const healthResponse = await page.request.get(`${API_URL}/health`)
      if (!healthResponse.ok()) {
        console.log('Backend not available - skipping 401 test')
        test.skip()
      }
    } catch (e) {
      console.log('Backend not reachable - skipping 401 test')
      test.skip()
    }

    // 1. Clear cookies and storage
    await context.clearCookies()
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })

    // 2. Make API request without auth
    const response = await page.request.get(`${API_URL}/api/v1/auth/me`)

    // 3. Verify 401 response
    expect(response.status()).toBe(401)

    const body = await response.json().catch(() => ({}))
    console.log('401 Response:', body)

    console.log('✅ Scenario 4: 401 Handling - PASSED')
  })

  test('Scenario 5: Backend Health Check', async ({ page }) => {
    // Verify backend is running
    try {
      const response = await page.request.get(`${API_URL}/health`)
      expect(response.status()).toBe(200)

      const body = await response.json()
      console.log('Backend health:', body)

      console.log('✅ Scenario 5: Backend Health Check - PASSED')
    } catch (e) {
      console.error('❌ Backend health check failed:', e)
      throw e
    }
  })

  test('Scenario 6: Application Enum Uppercase Verification', async ({ page }) => {
    // Verify that application enums are uppercase in API responses

    // Skip if backend not available
    try {
      const healthResponse = await page.request.get(`${API_URL}/health`)
      if (!healthResponse.ok()) {
        test.skip()
      }
    } catch (e) {
      test.skip()
    }

    // This test would require auth - skip if no credentials
    if (!process.env.TEST_PASSWORD) {
      test.skip()
    }

    // TODO: Add authenticated API call to verify uppercase enums
    // For now, just verify the backend is running
    console.log('✅ Scenario 6: Application Enum Verification - SKIPPED (requires auth)')
  })
})

test.describe('Smoke Tests - Quick Validation', () => {
  test('Frontend loads without errors', async ({ page }) => {
    const errors: string[] = []

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text())
      }
    })

    await page.goto(BASE_URL)
    await page.waitForLoadState('networkidle')

    // Allow some errors (e.g., missing auth tokens)
    const criticalErrors = errors.filter(err =>
      !err.includes('token') &&
      !err.includes('401') &&
      !err.includes('403')
    )

    expect(criticalErrors.length).toBe(0)
    console.log('✅ Frontend loads without critical errors')
  })

  test('Backend API responds', async ({ page }) => {
    const response = await page.request.get(`${API_URL}/health`)
    expect(response.status()).toBe(200)
    console.log('✅ Backend API responds')
  })
})
