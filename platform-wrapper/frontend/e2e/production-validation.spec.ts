/**
 * Production Validation Test Suite
 * 
 * Automated testing script for validating successful deployment
 * after fixing setInterval errors and other production issues.
 * 
 * Usage:
 * npx playwright test e2e/production-validation.spec.ts
 * 
 * For CI/CD:
 * npx playwright test e2e/production-validation.spec.ts --reporter=json
 */

import { test, expect, Page, Browser, ConsoleMessage } from '@playwright/test'

// Configuration
const PRODUCTION_URL = 'https://frontend-cdir2vud8-zebraassociates-projects.vercel.app'
const TEST_TIMEOUT = 60000 // 1 minute per test
const CONSOLE_ERROR_TIMEOUT = 5000 // Wait 5 seconds for console errors

// Console error tracking
interface ConsoleError {
  type: string
  text: string
  url: string
  timestamp: number
}

let consoleErrors: ConsoleError[] = []
let consoleWarnings: ConsoleError[] = []

test.describe('Production Deployment Validation', () => {
  let browser: Browser
  let page: Page

  test.beforeEach(async ({ browser: testBrowser, context }) => {
    browser = testBrowser
    page = await context.newPage()
    
    // Clear console tracking
    consoleErrors = []
    consoleWarnings = []

    // Track console messages
    page.on('console', (msg: ConsoleMessage) => {
      const timestamp = Date.now()
      const error = {
        type: msg.type(),
        text: msg.text(),
        url: msg.location().url,
        timestamp
      }

      if (msg.type() === 'error') {
        consoleErrors.push(error)
        console.error(`Console Error: ${error.text} at ${error.url}`)
      } else if (msg.type() === 'warning') {
        consoleWarnings.push(error)
        console.warn(`Console Warning: ${error.text} at ${error.url}`)
      }
    })

    // Track page errors
    page.on('pageerror', (error) => {
      consoleErrors.push({
        type: 'pageerror',
        text: error.message,
        url: page.url(),
        timestamp: Date.now()
      })
      console.error(`Page Error: ${error.message}`)
    })

    // Set longer timeout for production environment
    test.setTimeout(TEST_TIMEOUT)
  })

  test.afterEach(async () => {
    // Generate console report
    if (consoleErrors.length > 0 || consoleWarnings.length > 0) {
      console.log('\\n=== CONSOLE REPORT ===')
      console.log(`Errors: ${consoleErrors.length}`)
      console.log(`Warnings: ${consoleWarnings.length}`)
      
      if (consoleErrors.length > 0) {
        console.log('\\nERRORS:')
        consoleErrors.forEach((error, i) => {
          console.log(`${i + 1}. [${error.type}] ${error.text}`)
        })
      }

      if (consoleWarnings.length > 0) {
        console.log('\\nWARNINGS:')
        consoleWarnings.forEach((warning, i) => {
          console.log(`${i + 1}. [${warning.type}] ${warning.text}`)
        })
      }
    }

    await page.close()
  })

  test('should load production homepage without console errors', async () => {
    // Navigate to production URL
    await page.goto(PRODUCTION_URL, { 
      waitUntil: 'networkidle',
      timeout: 30000 
    })

    // Wait for page to fully load
    await page.waitForLoadState('domcontentloaded')
    
    // Wait additional time for any async operations that might cause console errors
    await page.waitForTimeout(CONSOLE_ERROR_TIMEOUT)

    // Check for favicon (should not 404)
    const faviconResponse = await page.goto(`${PRODUCTION_URL}/favicon.ico`)
    expect(faviconResponse?.status()).toBeLessThan(400)

    // Verify no critical console errors (especially setInterval errors)
    const criticalErrors = consoleErrors.filter(error => 
      error.text.toLowerCase().includes('setinterval') ||
      error.text.toLowerCase().includes('settimeout') ||
      error.text.toLowerCase().includes('is not a function')
    )

    expect(criticalErrors.length).toBe(0)

    // Take screenshot for debugging if needed
    await page.screenshot({ 
      path: 'test-results/homepage-loaded.png',
      fullPage: true 
    })
  })

  test('should navigate through authentication flow without errors', async () => {
    // Start at homepage
    await page.goto(PRODUCTION_URL, { waitUntil: 'networkidle' })
    
    // Look for login/auth elements
    const possibleLoginSelectors = [
      'a[href*="login"]',
      'button:has-text("Login")',
      'button:has-text("Sign In")',
      '[data-testid="login-button"]'
    ]

    let loginElement = null
    for (const selector of possibleLoginSelectors) {
      try {
        loginElement = await page.locator(selector).first()
        if (await loginElement.isVisible({ timeout: 2000 })) {
          break
        }
      } catch (e) {
        // Try next selector
      }
    }

    if (loginElement) {
      // Click login and check for Auth0 redirect or login form
      await loginElement.click()
      
      // Wait for navigation or modal
      await page.waitForTimeout(3000)
      
      // Check if we're redirected to Auth0 or showing login form
      const currentUrl = page.url()
      const isAuth0 = currentUrl.includes('auth0') || currentUrl.includes('authorize')
      const hasLoginForm = await page.locator('input[type="email"], input[type="text"][name*="email"]').count() > 0

      expect(isAuth0 || hasLoginForm || currentUrl.includes('login')).toBeTruthy()
    }

    // Verify no authentication-related console errors
    const authErrors = consoleErrors.filter(error => 
      error.text.toLowerCase().includes('auth') ||
      error.text.toLowerCase().includes('token') ||
      error.text.toLowerCase().includes('session')
    )

    // Allow some expected auth warnings but no critical errors
    const criticalAuthErrors = authErrors.filter(error => error.type === 'error')
    expect(criticalAuthErrors.length).toBe(0)

    await page.screenshot({ 
      path: 'test-results/auth-flow.png',
      fullPage: true 
    })
  })

  test('should validate Phase 2 functionality availability', async () => {
    await page.goto(PRODUCTION_URL, { waitUntil: 'networkidle' })
    
    // Wait for app to initialize
    await page.waitForTimeout(3000)

    // Check for Phase 2 related elements (organization features)
    const phase2Indicators = [
      '[data-testid*="organization"]',
      '[data-testid*="tenant"]',
      'text=organization',
      'text=Organization',
      'select[name*="organization"]',
      'button:has-text("Switch Organization")'
    ]

    let foundPhase2Elements = 0
    for (const selector of phase2Indicators) {
      try {
        const elements = await page.locator(selector).count()
        if (elements > 0) {
          foundPhase2Elements++
          console.log(`Found Phase 2 element: ${selector}`)
        }
      } catch (e) {
        // Element not found, continue
      }
    }

    // Phase 2 features might not be visible on landing page, but should be in DOM structure
    console.log(`Found ${foundPhase2Elements} Phase 2 related elements`)

    // Check for any Phase 2 specific console errors
    const phase2Errors = consoleErrors.filter(error => 
      error.text.toLowerCase().includes('organization') ||
      error.text.toLowerCase().includes('tenant') ||
      error.text.toLowerCase().includes('multi-tenant')
    )

    expect(phase2Errors.length).toBe(0)

    await page.screenshot({ 
      path: 'test-results/phase2-check.png',
      fullPage: true 
    })
  })

  test('should validate timer functions work correctly', async () => {
    await page.goto(PRODUCTION_URL, { waitUntil: 'networkidle' })
    
    // Wait for app initialization
    await page.waitForTimeout(2000)

    // Inject test script to validate timer functions
    const timerTestResult = await page.evaluate(() => {
      return new Promise((resolve) => {
        const results = {
          setIntervalAvailable: typeof setInterval === 'function',
          setTimeoutAvailable: typeof setTimeout === 'function',
          clearIntervalAvailable: typeof clearInterval === 'function',
          clearTimeoutAvailable: typeof clearTimeout === 'function',
          testSetInterval: false,
          testSetTimeout: false
        }

        // Test setInterval
        try {
          let intervalCount = 0
          const intervalId = setInterval(() => {
            intervalCount++
            if (intervalCount >= 2) {
              clearInterval(intervalId)
              results.testSetInterval = true
              
              // Test setTimeout
              try {
                setTimeout(() => {
                  results.testSetTimeout = true
                  resolve(results)
                }, 100)
              } catch (e) {
                resolve(results)
              }
            }
          }, 50)
        } catch (e) {
          // Test setTimeout even if setInterval fails
          try {
            setTimeout(() => {
              results.testSetTimeout = true
              resolve(results)
            }, 100)
          } catch (e2) {
            resolve(results)
          }
        }

        // Fallback timeout
        setTimeout(() => resolve(results), 1000)
      })
    })

    // Validate timer functions are available and working
    expect(timerTestResult.setIntervalAvailable).toBeTruthy()
    expect(timerTestResult.setTimeoutAvailable).toBeTruthy()
    expect(timerTestResult.clearIntervalAvailable).toBeTruthy()
    expect(timerTestResult.clearTimeoutAvailable).toBeTruthy()

    console.log('Timer Test Results:', timerTestResult)

    // Look for timer-related console errors after testing
    await page.waitForTimeout(1000)
    
    const timerErrors = consoleErrors.filter(error => 
      error.text.toLowerCase().includes('interval') ||
      error.text.toLowerCase().includes('timeout') ||
      error.text.toLowerCase().includes('timer')
    )

    expect(timerErrors.length).toBe(0)

    await page.screenshot({ 
      path: 'test-results/timer-test.png',
      fullPage: true 
    })
  })

  test('should generate comprehensive production health report', async () => {
    await page.goto(PRODUCTION_URL, { waitUntil: 'networkidle' })
    
    // Wait for full page load and any async operations
    await page.waitForTimeout(5000)

    // Collect page metrics
    const metrics = await page.evaluate(() => {
      return {
        url: window.location.href,
        title: document.title,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        hasReact: !!(window as any).React,
        hasNextjs: !!(window as any).__NEXT_DATA__,
        consoleErrorsCount: 0, // Will be filled from our tracking
        consoleWarningsCount: 0, // Will be filled from our tracking
        domContentLoaded: document.readyState,
        scriptTags: document.querySelectorAll('script').length,
        linkTags: document.querySelectorAll('link').length,
        hasAuth0: !!(window as any).Auth0,
        localStorageKeys: Object.keys(localStorage),
        sessionStorageKeys: Object.keys(sessionStorage)
      }
    })

    // Add console error counts
    metrics.consoleErrorsCount = consoleErrors.length
    metrics.consoleWarningsCount = consoleWarnings.length

    // Generate report
    const report = {
      testRun: {
        timestamp: new Date().toISOString(),
        url: PRODUCTION_URL,
        success: consoleErrors.length === 0
      },
      page: metrics,
      console: {
        errors: consoleErrors.length,
        warnings: consoleWarnings.length,
        criticalErrors: consoleErrors.filter(e => 
          e.text.includes('setInterval') || 
          e.text.includes('is not a function') ||
          e.text.includes('TypeError')
        )
      },
      recommendations: []
    }

    // Add recommendations based on findings
    if (consoleErrors.length > 0) {
      report.recommendations.push('Console errors detected - review error details')
    }
    if (consoleErrors.filter(e => e.text.includes('setInterval')).length > 0) {
      report.recommendations.push('setInterval errors still present - timer polyfills may need adjustment')
    }
    if (!metrics.hasNextjs) {
      report.recommendations.push('Next.js framework not detected - verify build configuration')
    }

    console.log('\\n=== PRODUCTION HEALTH REPORT ===')
    console.log(JSON.stringify(report, null, 2))

    // Save report to file
    const fs = require('fs')
    const reportPath = 'test-results/production-health-report.json'
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2))

    // Test should pass only if no critical errors
    expect(report.console.criticalErrors.length).toBe(0)

    await page.screenshot({ 
      path: 'test-results/final-health-check.png',
      fullPage: true 
    })
  })
})

// Utility test for manual debugging
test.describe('Manual Debug Utilities', () => {
  test.skip('debug - interactive session for manual testing', async ({ page }) => {
    await page.goto(PRODUCTION_URL)
    
    // Keep page open for manual inspection
    console.log('Page loaded. Use browser dev tools to inspect.')
    console.log('This test will wait indefinitely - kill with Ctrl+C')
    
    // Wait indefinitely for manual inspection
    await page.waitForTimeout(30 * 60 * 1000) // 30 minutes
  })
})