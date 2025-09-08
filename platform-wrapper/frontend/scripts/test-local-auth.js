#!/usr/bin/env node

/**
 * Local Development Authentication Test Script
 * Tests the complete authentication flow in local development
 */

const fetch = require('node-fetch')
const API_BASE = 'http://localhost:8000'
const FRONTEND_ORIGIN = 'http://localhost:3000'

async function testAuthFlow() {
  console.log('🧪 Testing Local Development Authentication Flow')
  console.log('=' .repeat(60))
  
  let allPassed = true
  
  // Test 1: Backend Health Check
  console.log('\n1. Testing Backend Health...')
  try {
    const response = await fetch(`${API_BASE}/health`)
    const data = await response.json()
    
    if (response.ok) {
      console.log('✅ Backend Health: OK')
      console.log(`   Version: ${data.version}`)
      console.log(`   CORS Mode: ${data.cors_mode}`)
    } else {
      console.log('❌ Backend Health: FAILED')
      console.log(`   Status: ${response.status}`)
      allPassed = false
    }
  } catch (error) {
    console.log('❌ Backend Health: CONNECTION FAILED')
    console.log(`   Error: ${error.message}`)
    allPassed = false
  }

  // Test 2: CORS Configuration
  console.log('\n2. Testing CORS Configuration...')
  try {
    const response = await fetch(`${API_BASE}/cors-debug`, {
      headers: {
        'Origin': FRONTEND_ORIGIN
      }
    })
    const data = await response.json()
    
    if (response.ok) {
      console.log('✅ CORS Configuration: OK')
      console.log(`   Request Origin: ${data.request_origin}`)
      console.log(`   Origin Allowed: ${data.origin_allowed}`)
      console.log(`   Configured Origins: ${data.cors_origins_configured.length} origins`)
      
      if (!data.origin_allowed) {
        console.log('⚠️  WARNING: Frontend origin not allowed')
        console.log(`   Frontend: ${FRONTEND_ORIGIN}`)
        console.log(`   Allowed: ${data.cors_origins_configured.join(', ')}`)
        allPassed = false
      }
    } else {
      console.log('❌ CORS Configuration: FAILED')
      console.log(`   Status: ${response.status}`)
      allPassed = false
    }
  } catch (error) {
    console.log('❌ CORS Configuration: CONNECTION FAILED')
    console.log(`   Error: ${error.message}`)
    allPassed = false
  }

  // Test 3: CORS Preflight
  console.log('\n3. Testing CORS Preflight...')
  try {
    const response = await fetch(`${API_BASE}/api/v1/auth/auth0-url`, {
      method: 'OPTIONS',
      headers: {
        'Origin': FRONTEND_ORIGIN,
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type'
      }
    })
    
    if (response.ok || response.status === 204) {
      console.log('✅ CORS Preflight: OK')
      console.log(`   Status: ${response.status}`)
      
      const corsHeaders = {
        'Access-Control-Allow-Origin': response.headers.get('access-control-allow-origin'),
        'Access-Control-Allow-Methods': response.headers.get('access-control-allow-methods'),
        'Access-Control-Allow-Headers': response.headers.get('access-control-allow-headers')
      }
      
      console.log('   Headers:', corsHeaders)
    } else {
      console.log('❌ CORS Preflight: FAILED')
      console.log(`   Status: ${response.status}`)
      allPassed = false
    }
  } catch (error) {
    console.log('❌ CORS Preflight: CONNECTION FAILED')
    console.log(`   Error: ${error.message}`)
    allPassed = false
  }

  // Test 4: Auth0 URL Endpoint
  console.log('\n4. Testing Auth0 URL Endpoint...')
  try {
    const redirectUri = `${FRONTEND_ORIGIN}/callback`
    const response = await fetch(`${API_BASE}/api/v1/auth/auth0-url?redirect_uri=${encodeURIComponent(redirectUri)}`, {
      headers: {
        'Origin': FRONTEND_ORIGIN
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      console.log('✅ Auth0 URL Endpoint: OK')
      console.log(`   Auth URL: ${data.auth_url.substring(0, 50)}...`)
      console.log(`   Redirect URI: ${data.redirect_uri}`)
      console.log(`   Scopes: ${data.scopes.join(', ')}`)
    } else {
      console.log('❌ Auth0 URL Endpoint: FAILED')
      console.log(`   Status: ${response.status}`)
      const errorText = await response.text()
      console.log(`   Response: ${errorText.substring(0, 200)}`)
      allPassed = false
    }
  } catch (error) {
    console.log('❌ Auth0 URL Endpoint: CONNECTION FAILED')
    console.log(`   Error: ${error.message}`)
    allPassed = false
  }

  // Test 5: Protected Endpoint (should fail without auth)
  console.log('\n5. Testing Protected Endpoint (Expected 403)...')
  try {
    const response = await fetch(`${API_BASE}/api/v1/organisations/industries`, {
      headers: {
        'Origin': FRONTEND_ORIGIN
      }
    })
    
    if (response.status === 403) {
      console.log('✅ Protected Endpoint: CORRECTLY PROTECTED')
      console.log('   Status: 403 Forbidden (as expected)')
    } else if (response.status === 401) {
      console.log('✅ Protected Endpoint: CORRECTLY PROTECTED')
      console.log('   Status: 401 Unauthorized (as expected)')
    } else {
      console.log('⚠️  Protected Endpoint: UNEXPECTED RESPONSE')
      console.log(`   Status: ${response.status} (expected 401/403)`)
    }
  } catch (error) {
    console.log('❌ Protected Endpoint: CONNECTION FAILED')
    console.log(`   Error: ${error.message}`)
    allPassed = false
  }

  // Summary
  console.log('\n' + '=' .repeat(60))
  if (allPassed) {
    console.log('🎉 ALL TESTS PASSED!')
    console.log('\nLocal development environment is ready:')
    console.log(`   Frontend: ${FRONTEND_ORIGIN}`)
    console.log(`   Backend: ${API_BASE}`)
    console.log(`   Auth0 Callback: ${FRONTEND_ORIGIN}/callback`)
    console.log('\nTo test authentication:')
    console.log(`1. Visit ${FRONTEND_ORIGIN}`)
    console.log('2. Click Login button')
    console.log('3. Complete Auth0 flow')
    console.log('4. Check AuthDebugPanel for token status')
  } else {
    console.log('❌ SOME TESTS FAILED!')
    console.log('\nCheck the failed tests above and:')
    console.log('1. Ensure backend is running on port 8000')
    console.log('2. Verify CORS configuration in backend/.env')
    console.log('3. Check Auth0 configuration')
    console.log('4. Review LOCAL_DEVELOPMENT_SETUP.md')
  }
}

// Run the tests
testAuthFlow().catch(console.error)