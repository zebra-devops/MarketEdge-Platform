#!/usr/bin/env node

/**
 * Zebra Associates Smoke Test Runner
 *
 * Standalone test runner for sales demos and manual verification
 * Can be run independently of the full Playwright test suite
 *
 * Usage:
 *   node scripts/zebra-smoke.js
 *
 * Environment Variables:
 *   BACKEND_URL - Backend API URL (default: http://localhost:8000)
 *   FRONTEND_URL - Frontend URL (default: http://localhost:3000)
 *   AUTH0_TEST_EMAIL - Test email for Auth0 login
 *   AUTH0_TEST_PASSWORD - Test password for Auth0 login
 */

const https = require('https')
const http = require('http')

// Configuration
const config = {
  backendUrl: process.env.BACKEND_URL || 'http://localhost:8000',
  frontendUrl: process.env.FRONTEND_URL || 'http://localhost:3000',
  zebraEmail: process.env.ZEBRA_TEST_EMAIL || 'devops@zebra.associates',
  zebraTenantId: '835d4f24-cff2-43e8-a470-93216a3d99a3',
  timeout: 60000 // 60 second timeout per US-0 requirements
}

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
}

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`)
}

function logSuccess(message) {
  log(`✅ ${message}`, colors.green)
}

function logError(message) {
  log(`❌ ${message}`, colors.red)
}

function logWarning(message) {
  log(`⚠️  ${message}`, colors.yellow)
}

function logInfo(message) {
  log(`ℹ️  ${message}`, colors.cyan)
}

function logHeader(message) {
  log('\n' + '='.repeat(80), colors.bright)
  log(message, colors.bright)
  log('='.repeat(80), colors.bright)
}

/**
 * Make HTTP/HTTPS request
 */
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url)
    const client = urlObj.protocol === 'https:' ? https : http

    const requestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: options.headers || {},
      timeout: options.timeout || 10000
    }

    const req = client.request(requestOptions, (res) => {
      let data = ''

      res.on('data', (chunk) => {
        data += chunk
      })

      res.on('end', () => {
        resolve({
          status: res.statusCode,
          statusText: res.statusMessage,
          headers: res.headers,
          data: data
        })
      })
    })

    req.on('error', (error) => {
      reject(error)
    })

    req.on('timeout', () => {
      req.destroy()
      reject(new Error('Request timeout'))
    })

    if (options.body) {
      req.write(options.body)
    }

    req.end()
  })
}

/**
 * Test 1: Backend Health Check
 */
async function testBackendHealth() {
  logInfo('Testing backend health...')

  try {
    const response = await makeRequest(`${config.backendUrl}/health`)

    if (response.status === 200) {
      logSuccess('Backend is healthy')
      return true
    } else {
      logError(`Backend health check failed: ${response.status} ${response.statusText}`)
      return false
    }
  } catch (error) {
    logError(`Backend health check error: ${error.message}`)
    return false
  }
}

/**
 * Test 2: Frontend Accessibility
 */
async function testFrontendAccess() {
  logInfo('Testing frontend accessibility...')

  try {
    const response = await makeRequest(config.frontendUrl)

    if (response.status === 200) {
      logSuccess('Frontend is accessible')
      return true
    } else {
      logError(`Frontend access failed: ${response.status} ${response.statusText}`)
      return false
    }
  } catch (error) {
    logError(`Frontend access error: ${error.message}`)
    return false
  }
}

/**
 * Test 3: Auth0 Authorization URL Generation
 */
async function testAuth0UrlGeneration() {
  logInfo('Testing Auth0 URL generation...')

  try {
    const redirectUri = encodeURIComponent(`${config.frontendUrl}/callback`)
    const response = await makeRequest(
      `${config.backendUrl}/api/v1/auth/auth0-url?redirect_uri=${redirectUri}`
    )

    if (response.status === 200) {
      const data = JSON.parse(response.data)
      if (data.auth_url && data.auth_url.includes('auth0.com')) {
        logSuccess('Auth0 URL generation working')
        logInfo(`Auth0 URL: ${data.auth_url.substring(0, 80)}...`)
        return true
      } else {
        logError('Auth0 URL format invalid')
        return false
      }
    } else {
      logError(`Auth0 URL generation failed: ${response.status} ${response.statusText}`)
      return false
    }
  } catch (error) {
    logError(`Auth0 URL generation error: ${error.message}`)
    return false
  }
}

/**
 * Test 4: Application Routes Accessibility
 */
async function testApplicationRoutes() {
  logInfo('Testing application routes...')

  const routes = [
    { name: 'Dashboard', path: '/' },
    { name: 'Market Edge', path: '/market-edge' },
    { name: 'Causal Edge', path: '/causal-edge' },
    { name: 'Value Edge', path: '/value-edge' },
    { name: 'Admin Panel', path: '/admin' }
  ]

  let allPassed = true

  for (const route of routes) {
    try {
      const response = await makeRequest(`${config.frontendUrl}${route.path}`)

      if (response.status === 200) {
        logSuccess(`${route.name} route accessible`)
      } else if (response.status === 404) {
        logWarning(`${route.name} route not found (${response.status})`)
        allPassed = false
      } else {
        logError(`${route.name} route failed: ${response.status}`)
        allPassed = false
      }
    } catch (error) {
      logError(`${route.name} route error: ${error.message}`)
      allPassed = false
    }
  }

  return allPassed
}

/**
 * Test 5: API Endpoints Availability
 */
async function testApiEndpoints() {
  logInfo('Testing API endpoints...')

  const endpoints = [
    { name: 'Health', path: '/health' },
    { name: 'Auth Me', path: '/api/v1/auth/me' },
    { name: 'Organisations', path: '/api/v1/organisations' },
    { name: 'Users', path: '/api/v1/users' }
  ]

  let allPassed = true

  for (const endpoint of endpoints) {
    try {
      const response = await makeRequest(`${config.backendUrl}${endpoint.path}`)

      // For protected endpoints, expect 401 (not 500 or 404)
      if (response.status === 200 || response.status === 401) {
        logSuccess(`${endpoint.name} endpoint available`)
      } else if (response.status === 404) {
        logError(`${endpoint.name} endpoint not found`)
        allPassed = false
      } else if (response.status === 500) {
        logError(`${endpoint.name} endpoint server error`)
        allPassed = false
      } else {
        logWarning(`${endpoint.name} endpoint: ${response.status}`)
      }
    } catch (error) {
      logError(`${endpoint.name} endpoint error: ${error.message}`)
      allPassed = false
    }
  }

  return allPassed
}

/**
 * Main test runner
 */
async function runTests() {
  const startTime = Date.now()

  logHeader('🦓 ZEBRA ASSOCIATES SMOKE TEST')
  logInfo(`Backend: ${config.backendUrl}`)
  logInfo(`Frontend: ${config.frontendUrl}`)
  logInfo(`Zebra Email: ${config.zebraEmail}`)
  logInfo(`Timeout: ${config.timeout}ms`)

  const results = {
    backendHealth: false,
    frontendAccess: false,
    auth0UrlGeneration: false,
    applicationRoutes: false,
    apiEndpoints: false
  }

  try {
    // Run tests sequentially
    log('\n📡 Phase 1: Infrastructure Tests', colors.bright)
    results.backendHealth = await testBackendHealth()
    results.frontendAccess = await testFrontendAccess()

    log('\n🔐 Phase 2: Authentication Tests', colors.bright)
    results.auth0UrlGeneration = await testAuth0UrlGeneration()

    log('\n🚀 Phase 3: Application Tests', colors.bright)
    results.applicationRoutes = await testApplicationRoutes()
    results.apiEndpoints = await testApiEndpoints()

  } catch (error) {
    logError(`Test execution error: ${error.message}`)
  }

  // Calculate results
  const duration = Date.now() - startTime
  const passedTests = Object.values(results).filter(r => r).length
  const totalTests = Object.keys(results).length
  const allPassed = passedTests === totalTests

  // Print summary
  logHeader('📊 TEST SUMMARY')
  log(`Duration: ${duration}ms (limit: ${config.timeout}ms)`, duration < config.timeout ? colors.green : colors.red)
  log(`Tests Passed: ${passedTests}/${totalTests}`, allPassed ? colors.green : colors.red)
  log('')

  Object.entries(results).forEach(([test, passed]) => {
    const testName = test.replace(/([A-Z])/g, ' $1').trim()
    const testNameCapitalized = testName.charAt(0).toUpperCase() + testName.slice(1)
    log(`  ${passed ? '✅' : '❌'} ${testNameCapitalized}`, passed ? colors.green : colors.red)
  })

  log('')
  if (allPassed && duration < config.timeout) {
    logHeader('✅ ALL TESTS PASSED - £925K OPPORTUNITY PROTECTED')
    process.exit(0)
  } else {
    logHeader('❌ TESTS FAILED - ZEBRA ASSOCIATES ACCESS AT RISK')
    logWarning('Please fix failing tests before merging authentication changes')
    process.exit(1)
  }
}

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  logError(`Uncaught exception: ${error.message}`)
  process.exit(1)
})

process.on('unhandledRejection', (error) => {
  logError(`Unhandled rejection: ${error.message}`)
  process.exit(1)
})

// Run tests
runTests()