/**
 * Comprehensive Authentication Database Diagnosis Test Suite
 * 
 * This test suite performs end-to-end testing of the MarketEdge authentication system
 * to identify the exact failure point causing persistent 500 "Database error occurred" 
 * messages despite multiple fixes.
 * 
 * CRITICAL SITUATION CONTEXT:
 * - Test codes return 400 (correct) but real Auth0 tokens return 500 (broken)
 * - Multiple database fixes applied but still getting 500 errors
 * - Need to identify exact failure point in authentication flow
 */

import { test, expect, Page, Request, Response } from '@playwright/test'

// Configuration
const FRONTEND_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000'
const BACKEND_URL = 'https://marketedge-platform.onrender.com' // Current production backend
const AUTH0_DOMAIN = 'dev-m4n2k4u7xhbj3lqn.us.auth0.com' // From Auth0 config

// Network monitoring interfaces
interface NetworkRequest {
  url: string
  method: string
  headers: Record<string, string>
  postData?: string
  timestamp: number
}

interface NetworkResponse {
  url: string
  status: number
  statusText: string
  headers: Record<string, string>
  body?: string
  timestamp: number
}

interface AuthFlowEvent {
  type: 'request' | 'response' | 'redirect' | 'error'
  url: string
  status?: number
  data?: any
  timestamp: number
  step: string
}

// Global tracking variables
let networkRequests: NetworkRequest[] = []
let networkResponses: NetworkResponse[] = []
let authFlowEvents: AuthFlowEvent[] = []
let consoleMessages: any[] = []

test.describe('Authentication Database Diagnosis', () => {
  
  test.beforeEach(async ({ page }) => {
    // Reset tracking arrays
    networkRequests = []
    networkResponses = []
    authFlowEvents = []
    consoleMessages = []

    // Set up comprehensive network monitoring
    page.on('request', (request: Request) => {
      const networkRequest: NetworkRequest = {
        url: request.url(),
        method: request.method(),
        headers: request.headers(),
        postData: request.postData() || undefined,
        timestamp: Date.now()
      }
      networkRequests.push(networkRequest)
      
      // Log auth-related requests
      if (request.url().includes('/api/v1/auth/') || 
          request.url().includes('auth0') || 
          request.url().includes('/login')) {
        authFlowEvents.push({
          type: 'request',
          url: request.url(),
          data: {
            method: request.method(),
            headers: request.headers(),
            postData: request.postData()
          },
          timestamp: Date.now(),
          step: 'auth_request'
        })
        console.log(`🔍 AUTH REQUEST: ${request.method()} ${request.url()}`)
      }
    })

    page.on('response', async (response: Response) => {
      let body: string | undefined
      try {
        // Capture response body for auth endpoints
        if (response.url().includes('/api/v1/auth/') || 
            response.url().includes('auth0')) {
          body = await response.text()
        }
      } catch (e) {
        // Some responses can't be read
      }

      const networkResponse: NetworkResponse = {
        url: response.url(),
        status: response.status(),
        statusText: response.statusText(),
        headers: response.headers(),
        body: body,
        timestamp: Date.now()
      }
      networkResponses.push(networkResponse)
      
      // Log auth-related responses
      if (response.url().includes('/api/v1/auth/') || 
          response.url().includes('auth0') || 
          response.url().includes('/login')) {
        authFlowEvents.push({
          type: 'response',
          url: response.url(),
          status: response.status(),
          data: {
            statusText: response.statusText(),
            headers: response.headers(),
            body: body
          },
          timestamp: Date.now(),
          step: 'auth_response'
        })
        console.log(`📡 AUTH RESPONSE: ${response.status()} ${response.url()}`)
        
        // Special handling for 500 errors
        if (response.status() === 500) {
          console.error(`❌ 500 ERROR DETECTED: ${response.url()}`)
          if (body) {
            console.error(`Error body: ${body}`)
          }
        }
      }
    })

    // Monitor console messages
    page.on('console', (msg) => {
      const consoleMessage = {
        type: msg.type(),
        text: msg.text(),
        location: msg.location(),
        timestamp: Date.now()
      }
      consoleMessages.push(consoleMessage)
      
      if (msg.type() === 'error') {
        console.error(`🚨 CONSOLE ERROR: ${msg.text()}`)
      }
    })

    // Monitor page errors
    page.on('pageerror', (error) => {
      console.error(`📄 PAGE ERROR: ${error.message}`)
      authFlowEvents.push({
        type: 'error',
        url: page.url(),
        data: {
          message: error.message,
          stack: error.stack
        },
        timestamp: Date.now(),
        step: 'page_error'
      })
    })
  })

  test('should diagnose auth endpoint response formats', async ({ page }) => {
    console.log('\n🔧 TESTING AUTH ENDPOINT RESPONSE FORMATS')
    
    // Test 1: Direct backend auth endpoint with test code
    console.log('\n1️⃣ Testing direct backend auth endpoint with test code...')
    
    const testAuthPayload = {
      code: 'test_diagnostic_code_playwright',
      redirect_uri: 'https://marketedge-platform.onrender.com/callback'
    }
    
    try {
      const response = await page.request.post(`${BACKEND_URL}/api/v1/auth/login`, {
        data: testAuthPayload,
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      console.log(`   Status: ${response.status()}`)
      console.log(`   Status Text: ${response.statusText()}`)
      
      const responseBody = await response.text()
      console.log(`   Response Body: ${responseBody.substring(0, 500)}...`)
      
      // Analyze response for database-specific errors
      if (response.status() === 500) {
        console.error('   ❌ 500 ERROR: Database operation failed')
        if (responseBody.includes('Database error occurred')) {
          console.error('   🚨 CONFIRMED: Database error message present')
        }
        if (responseBody.includes('enum')) {
          console.error('   🚨 ENUM ERROR: Database enum constraint violation')
        }
        if (responseBody.includes('organisation')) {
          console.error('   🚨 ORGANIZATION CREATION: Error during org creation')
        }
      } else if (response.status() === 400) {
        console.log('   ✅ EXPECTED: 400 for test code (auth validation working)')
      }
      
      // Store detailed response for analysis
      authFlowEvents.push({
        type: 'response',
        url: `${BACKEND_URL}/api/v1/auth/login`,
        status: response.status(),
        data: {
          body: responseBody,
          headers: response.headers()
        },
        timestamp: Date.now(),
        step: 'direct_test_auth'
      })
      
    } catch (error) {
      console.error(`   ❌ REQUEST FAILED: ${error}`)
    }
  })

  test('should test database operations independently', async ({ page }) => {
    console.log('\n🔧 TESTING DATABASE OPERATIONS INDEPENDENTLY')
    
    // Test database health endpoint
    console.log('\n1️⃣ Testing database health...')
    
    try {
      const healthResponse = await page.request.get(`${BACKEND_URL}/health`)
      console.log(`   Health Status: ${healthResponse.status()}`)
      
      if (healthResponse.ok()) {
        const healthData = await healthResponse.json()
        console.log(`   Health Data:`, healthData)
        
        if (healthData.database) {
          console.log('   ✅ Database connection reported healthy')
        } else {
          console.error('   ❌ Database connection issues reported')
        }
      }
    } catch (error) {
      console.error(`   ❌ Health check failed: ${error}`)
    }
    
    // Test specific database endpoints that might reveal constraints
    console.log('\n2️⃣ Testing user creation constraint validation...')
    
    const testUserData = {
      email: 'test-playwright-user@example.com',
      first_name: 'Test',
      last_name: 'User',
      organisation_name: 'Test Organization'
    }
    
    // This might reveal enum constraint issues
    try {
      const userTestResponse = await page.request.post(`${BACKEND_URL}/api/v1/users`, {
        data: testUserData,
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      console.log(`   User Creation Status: ${userTestResponse.status()}`)
      const userResponseBody = await userTestResponse.text()
      
      if (userTestResponse.status() === 500) {
        console.error('   🚨 USER CREATION 500 ERROR:')
        console.error(`   Error: ${userResponseBody}`)
        
        // Check for specific constraint violations
        if (userResponseBody.includes('enum') || userResponseBody.includes('constraint')) {
          console.error('   🚨 CONSTRAINT VIOLATION: Database enum or constraint issue')
        }
        if (userResponseBody.includes('industry_type') || userResponseBody.includes('subscription_plan')) {
          console.error('   🚨 ENUM FIELD ERROR: Industry or subscription enum issue')
        }
      }
      
    } catch (error) {
      console.error(`   ❌ User creation test failed: ${error}`)
    }
  })

  test('should monitor frontend authentication flow', async ({ page }) => {
    console.log('\n🔧 MONITORING FRONTEND AUTHENTICATION FLOW')
    
    // Navigate to the frontend
    console.log('\n1️⃣ Navigating to frontend...')
    await page.goto(FRONTEND_URL)
    
    // Wait for page to load
    await page.waitForLoadState('networkidle')
    
    // Look for login/authentication elements
    console.log('\n2️⃣ Looking for authentication elements...')
    
    const possibleLoginSelectors = [
      'button:has-text("Login")',
      'button:has-text("Sign In")',
      'a[href*="login"]',
      '[data-testid="login-button"]',
      'button:has-text("Get Started")'
    ]
    
    let loginButton = null
    for (const selector of possibleLoginSelectors) {
      try {
        const element = page.locator(selector).first()
        if (await element.isVisible({ timeout: 2000 })) {
          loginButton = element
          console.log(`   ✅ Found login element: ${selector}`)
          break
        }
      } catch (e) {
        // Continue to next selector
      }
    }
    
    if (loginButton) {
      console.log('\n3️⃣ Initiating authentication flow...')
      
      // Click login and monitor the flow
      await loginButton.click()
      
      // Wait for navigation or Auth0 redirect
      await page.waitForTimeout(3000)
      
      const currentUrl = page.url()
      console.log(`   Current URL after login click: ${currentUrl}`)
      
      if (currentUrl.includes('auth0')) {
        console.log('   ✅ Redirected to Auth0 - authentication flow initiated')
        
        // Monitor Auth0 flow without actually logging in
        // (This would require real credentials)
        console.log('   📋 Auth0 redirect successful - would require real credentials for full test')
        
        // Check for any immediate errors
        await page.waitForTimeout(2000)
        
        const pageErrors = consoleMessages.filter(msg => msg.type === 'error')
        if (pageErrors.length > 0) {
          console.error('   ❌ Errors detected during Auth0 redirect:')
          pageErrors.forEach(error => {
            console.error(`      ${error.text}`)
          })
        }
        
      } else if (currentUrl.includes('login')) {
        console.log('   📋 Navigated to login page')
        
        // Check for login form elements
        const emailInput = page.locator('input[type="email"]')
        const passwordInput = page.locator('input[type="password"]')
        
        if (await emailInput.isVisible() && await passwordInput.isVisible()) {
          console.log('   ✅ Login form detected')
        }
      }
    } else {
      console.log('   ⚠️  No login button found - checking if already authenticated')
    }
    
    // Check for any auth-related network activity
    const authRequests = networkRequests.filter(req => 
      req.url.includes('/auth/') || 
      req.url.includes('auth0')
    )
    
    console.log(`\n4️⃣ Network Analysis: ${authRequests.length} auth-related requests`)
    authRequests.forEach((req, index) => {
      console.log(`   ${index + 1}. ${req.method} ${req.url}`)
    })
    
    // Check responses
    const authResponses = networkResponses.filter(res => 
      res.url.includes('/auth/') || 
      res.url.includes('auth0')
    )
    
    console.log(`\n5️⃣ Response Analysis: ${authResponses.length} auth-related responses`)
    authResponses.forEach((res, index) => {
      console.log(`   ${index + 1}. ${res.status} ${res.url}`)
      if (res.status === 500) {
        console.error(`      🚨 500 ERROR: ${res.body}`)
      }
    })
  })

  test('should perform comprehensive error analysis', async ({ page }) => {
    console.log('\n🔧 PERFORMING COMPREHENSIVE ERROR ANALYSIS')
    
    // Test various authentication scenarios that might trigger the 500 error
    const testScenarios = [
      {
        name: 'JSON format with test code',
        payload: {
          code: 'test_code_json',
          redirect_uri: 'https://marketedge-platform.onrender.com/callback'
        },
        contentType: 'application/json'
      },
      {
        name: 'Form data format with test code',
        payload: 'code=test_code_form&redirect_uri=https://marketedge-platform.onrender.com/callback',
        contentType: 'application/x-www-form-urlencoded'
      },
      {
        name: 'JSON with Auth0-like code',
        payload: {
          code: 'AUTH0_TEST_CODE_12345678901234567890',
          redirect_uri: 'https://marketedge-platform.onrender.com/callback',
          state: 'test_state_value'
        },
        contentType: 'application/json'
      }
    ]
    
    for (let i = 0; i < testScenarios.length; i++) {
      const scenario = testScenarios[i]
      console.log(`\n${i + 1}️⃣ Testing scenario: ${scenario.name}`)
      
      try {
        const response = await page.request.post(`${BACKEND_URL}/api/v1/auth/login`, {
          data: scenario.payload,
          headers: {
            'Content-Type': scenario.contentType
          }
        })
        
        console.log(`   Status: ${response.status()} ${response.statusText()}`)
        
        const responseBody = await response.text()
        
        if (response.status() === 500) {
          console.error('   ❌ 500 ERROR DETAILS:')
          console.error(`      Body: ${responseBody}`)
          
          // Analyze specific error patterns
          if (responseBody.includes('Database error occurred')) {
            console.error('      🚨 Database error confirmed')
            
            if (responseBody.includes('enum')) {
              console.error('      🚨 ENUM constraint violation detected')
            }
            if (responseBody.includes('organisation') || responseBody.includes('organization')) {
              console.error('      🚨 Organization creation error detected')
            }
            if (responseBody.includes('industry_type')) {
              console.error('      🚨 Industry type enum error detected')
            }
            if (responseBody.includes('subscription_plan')) {
              console.error('      🚨 Subscription plan enum error detected')
            }
          }
          
          if (responseBody.includes('Auth0')) {
            console.error('      🚨 Auth0 integration error detected')
          }
          
        } else if (response.status() === 400) {
          console.log('   ✅ Expected 400 for test code')
          
          const errorData = JSON.parse(responseBody)
          console.log(`   Error message: ${errorData.detail || 'No detail available'}`)
          
        } else {
          console.log(`   ℹ️  Unexpected status: ${response.status()}`)
        }
        
      } catch (error) {
        console.error(`   ❌ Request failed: ${error}`)
      }
    }
  })

  test('should generate comprehensive diagnostic report', async ({ page }) => {
    console.log('\n🔧 GENERATING COMPREHENSIVE DIAGNOSTIC REPORT')
    
    // Run a quick test to gather current state
    await page.goto(FRONTEND_URL)
    await page.waitForLoadState('networkidle')
    
    // Test backend directly
    try {
      const backendHealthResponse = await page.request.get(`${BACKEND_URL}/health`)
      const backendHealth = {
        status: backendHealthResponse.status(),
        ok: backendHealthResponse.ok()
      }
      
      let healthData = null
      if (backendHealthResponse.ok()) {
        try {
          healthData = await backendHealthResponse.json()
        } catch (e) {
          healthData = { error: 'Could not parse health response' }
        }
      }
      
      // Test auth endpoint with diagnostic code
      const authTestResponse = await page.request.post(`${BACKEND_URL}/api/v1/auth/login`, {
        data: {
          code: 'PLAYWRIGHT_DIAGNOSTIC_TEST',
          redirect_uri: 'https://marketedge-platform.onrender.com/callback'
        },
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      const authTestBody = await authTestResponse.text()
      
      // Generate comprehensive report
      const diagnosticReport = {
        timestamp: new Date().toISOString(),
        test_environment: {
          frontend_url: FRONTEND_URL,
          backend_url: BACKEND_URL,
          auth0_domain: AUTH0_DOMAIN
        },
        backend_health: {
          ...backendHealth,
          health_data: healthData
        },
        auth_endpoint_test: {
          status: authTestResponse.status(),
          status_text: authTestResponse.statusText(),
          response_body: authTestBody,
          is_500_error: authTestResponse.status() === 500,
          has_database_error: authTestBody.includes('Database error occurred'),
          has_enum_error: authTestBody.includes('enum'),
          has_org_creation_error: authTestBody.includes('organisation') || authTestBody.includes('organization')
        },
        network_analysis: {
          total_requests: networkRequests.length,
          total_responses: networkResponses.length,
          auth_requests: networkRequests.filter(req => 
            req.url.includes('/auth/') || req.url.includes('auth0')
          ).length,
          error_responses: networkResponses.filter(res => res.status >= 400).length,
          five_hundred_errors: networkResponses.filter(res => res.status === 500).length
        },
        console_analysis: {
          total_messages: consoleMessages.length,
          error_messages: consoleMessages.filter(msg => msg.type === 'error').length,
          warning_messages: consoleMessages.filter(msg => msg.type === 'warning').length
        },
        auth_flow_events: authFlowEvents.length,
        recommendations: []
      }
      
      // Generate specific recommendations
      if (diagnosticReport.auth_endpoint_test.is_500_error) {
        if (diagnosticReport.auth_endpoint_test.has_database_error) {
          diagnosticReport.recommendations.push('CRITICAL: Database error confirmed in auth endpoint')
          
          if (diagnosticReport.auth_endpoint_test.has_enum_error) {
            diagnosticReport.recommendations.push('Database enum constraint violation - check Industry/SubscriptionPlan enum values')
          }
          
          if (diagnosticReport.auth_endpoint_test.has_org_creation_error) {
            diagnosticReport.recommendations.push('Organization creation failing - check default organization creation logic')
          }
        } else {
          diagnosticReport.recommendations.push('500 error without database message - check application error handling')
        }
      } else if (diagnosticReport.auth_endpoint_test.status === 400) {
        diagnosticReport.recommendations.push('Auth validation working correctly (400 for test code expected)')
      }
      
      if (diagnosticReport.backend_health.ok) {
        diagnosticReport.recommendations.push('Backend health check passing - application is running')
      } else {
        diagnosticReport.recommendations.push('CRITICAL: Backend health check failing')
      }
      
      // Output comprehensive report
      console.log('\n' + '='.repeat(80))
      console.log('COMPREHENSIVE AUTHENTICATION DIAGNOSTIC REPORT')
      console.log('='.repeat(80))
      console.log(JSON.stringify(diagnosticReport, null, 2))
      
      // Save report to file
      const fs = require('fs')
      const reportPath = 'test-results/auth-diagnostic-report.json'
      fs.writeFileSync(reportPath, JSON.stringify(diagnosticReport, null, 2))
      console.log(`\n📋 Report saved to: ${reportPath}`)
      
      // Final assessment
      if (diagnosticReport.auth_endpoint_test.has_database_error) {
        console.error('\n❌ DIAGNOSIS CONFIRMED: Database errors persist in authentication flow')
        console.error('🔍 Focus areas for fixes:')
        
        if (diagnosticReport.auth_endpoint_test.has_enum_error) {
          console.error('   - Database enum constraint issues')
        }
        if (diagnosticReport.auth_endpoint_test.has_org_creation_error) {
          console.error('   - Organization creation logic')
        }
        console.error('   - Database migration state')
        console.error('   - Environment variable configuration')
        
      } else if (diagnosticReport.auth_endpoint_test.status === 400) {
        console.log('\n✅ DIAGNOSIS: Authentication validation working, would likely succeed with real Auth0 token')
        
      } else {
        console.log('\n⚠️  DIAGNOSIS: Unexpected authentication behavior detected')
      }
      
      // Create screenshot for visual debugging
      await page.screenshot({ 
        path: 'test-results/auth-diagnosis-final.png',
        fullPage: true 
      })
      
    } catch (error) {
      console.error(`Diagnostic test failed: ${error}`)
    }
  })

  test.afterEach(async ({ page }) => {
    // Generate summary after each test
    console.log('\n' + '-'.repeat(50))
    console.log('TEST SUMMARY')
    console.log('-'.repeat(50))
    console.log(`Network Requests: ${networkRequests.length}`)
    console.log(`Network Responses: ${networkResponses.length}`)
    console.log(`Auth Flow Events: ${authFlowEvents.length}`)
    console.log(`Console Messages: ${consoleMessages.length}`)
    
    // Log any 500 errors detected
    const fiveHundredErrors = networkResponses.filter(res => res.status === 500)
    if (fiveHundredErrors.length > 0) {
      console.error(`🚨 500 ERRORS DETECTED: ${fiveHundredErrors.length}`)
      fiveHundredErrors.forEach((error, index) => {
        console.error(`   ${index + 1}. ${error.url}: ${error.body}`)
      })
    }
    
    console.log('-'.repeat(50))
  })
})

/**
 * Backend API Direct Testing Suite
 * Tests backend endpoints directly without frontend interaction
 */
test.describe('Backend API Direct Testing', () => {
  
  test('should test auth endpoint with different payload formats', async ({ request }) => {
    console.log('\n🔧 TESTING BACKEND AUTH ENDPOINT DIRECTLY')
    
    const testCases = [
      {
        name: 'Standard JSON format',
        data: { 
          code: 'test_code_standard', 
          redirect_uri: 'https://marketedge-platform.onrender.com/callback' 
        },
        headers: { 'Content-Type': 'application/json' }
      },
      {
        name: 'Form data format',
        data: 'code=test_code_form&redirect_uri=https://marketedge-platform.onrender.com/callback',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      },
      {
        name: 'JSON with additional Auth0 fields',
        data: { 
          code: 'test_code_extended', 
          redirect_uri: 'https://marketedge-platform.onrender.com/callback',
          state: 'test_state',
          scope: 'openid profile email'
        },
        headers: { 'Content-Type': 'application/json' }
      }
    ]
    
    for (const testCase of testCases) {
      console.log(`\n📋 Testing: ${testCase.name}`)
      
      try {
        const response = await request.post(`${BACKEND_URL}/api/v1/auth/login`, {
          data: testCase.data,
          headers: testCase.headers
        })
        
        const responseText = await response.text()
        
        console.log(`   Status: ${response.status()} ${response.statusText()}`)
        
        if (response.status() === 500) {
          console.error('   ❌ 500 ERROR:')
          console.error(`   Response: ${responseText}`)
          
          // Detailed error analysis
          if (responseText.includes('Database error occurred')) {
            console.error('   🚨 DATABASE ERROR CONFIRMED')
          }
          if (responseText.includes('enum')) {
            console.error('   🚨 ENUM CONSTRAINT VIOLATION')
          }
        } else if (response.status() === 400) {
          console.log('   ✅ Expected 400 (test code rejection)')
        }
        
      } catch (error) {
        console.error(`   ❌ Request failed: ${error}`)
      }
    }
  })

  test('should test database-related endpoints for constraint issues', async ({ request }) => {
    console.log('\n🔧 TESTING DATABASE CONSTRAINT VALIDATION')
    
    // Test health endpoint
    console.log('\n1️⃣ Testing health endpoint...')
    try {
      const healthResponse = await request.get(`${BACKEND_URL}/health`)
      console.log(`   Health Status: ${healthResponse.status()}`)
      
      if (healthResponse.ok()) {
        const healthData = await healthResponse.json()
        console.log('   Health Response:', JSON.stringify(healthData, null, 2))
      }
    } catch (error) {
      console.error(`   Health check failed: ${error}`)
    }
    
    // Test endpoints that might create organizations with enum constraints
    console.log('\n2️⃣ Testing organization creation constraints...')
    
    const orgTestData = {
      name: 'Test Organization Constraint Check',
      industry: 'Technology',
      industry_type: 'default',  // Test enum value
      subscription_plan: 'basic'  // Test enum value
    }
    
    try {
      const orgResponse = await request.post(`${BACKEND_URL}/api/v1/organisations`, {
        data: orgTestData,
        headers: { 'Content-Type': 'application/json' }
      })
      
      console.log(`   Org Creation Status: ${orgResponse.status()}`)
      
      if (orgResponse.status() === 500) {
        const errorBody = await orgResponse.text()
        console.error('   🚨 ORGANIZATION CREATION ERROR:')
        console.error(`   Error: ${errorBody}`)
        
        if (errorBody.includes('enum')) {
          console.error('   🚨 ENUM CONSTRAINT CONFIRMED')
        }
      }
    } catch (error) {
      console.error(`   Organization test failed: ${error}`)
    }
  })
})