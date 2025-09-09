/**
 * Authentication Flow Test Script
 * 
 * This script helps test the authentication fixes for the £925K Zebra Associates opportunity
 * Run this in the browser console to diagnose authentication issues
 */

console.log('🧪 Starting Authentication Flow Test for Zebra Associates...')

// Test 1: Check if auth debug functions are available
console.log('\n📋 Test 1: Auth Debug Functions Availability')
const debugFunctions = ['debugAuthState', 'testAdminApiAccess', 'refreshAndTest', 'emergencyTokenRecovery']
debugFunctions.forEach(func => {
  console.log(`   ${func}: ${typeof window[func] === 'function' ? '✅ Available' : '❌ Missing'}`)
})

// Test 2: Check storage mechanisms
console.log('\n📋 Test 2: Storage Mechanisms')
try {
  localStorage.setItem('test', 'test')
  localStorage.removeItem('test')
  console.log('   LocalStorage: ✅ Available')
} catch (e) {
  console.log('   LocalStorage: ❌ Blocked')
}

try {
  document.cookie = 'test=test'
  const cookiesWork = document.cookie.includes('test=test')
  if (cookiesWork) {
    // Clean up
    document.cookie = 'test=; expires=Thu, 01 Jan 1970 00:00:00 GMT'
  }
  console.log(`   Cookies: ${cookiesWork ? '✅ Available' : '❌ Blocked'}`)
} catch (e) {
  console.log('   Cookies: ❌ Error')
}

// Test 3: Check current authentication state
console.log('\n📋 Test 3: Current Authentication State')
if (typeof window.debugAuthState === 'function') {
  window.debugAuthState()
} else {
  console.log('   ❌ Debug functions not available - page may need refresh')
}

// Test 4: Check if we're on the right domain
console.log('\n📋 Test 4: Environment Check')
console.log('   Current URL:', window.location.href)
console.log('   Expected domains: app.zebra.associates (production) or localhost (development)')
console.log('   API Base URL:', process.env.NEXT_PUBLIC_API_BASE_URL || 'Not set')

// Test 5: Manual token check
console.log('\n📋 Test 5: Manual Token Check')
const localToken = localStorage.getItem('access_token')
const cookieToken = document.cookie.split(';').find(cookie => cookie.trim().startsWith('access_token='))
const storedUser = localStorage.getItem('current_user')

console.log('   LocalStorage Token:', localToken ? `Found (${localToken.length} chars)` : 'Not found')
console.log('   Cookie Token:', cookieToken ? 'Found' : 'Not found')
console.log('   Stored User:', storedUser ? JSON.parse(storedUser).email : 'Not found')

// Instructions
console.log('\n📋 Next Steps for Testing:')
console.log('1. If auth debug functions are available, run: debugAuthState()')
console.log('2. If you have admin access, run: testAdminApiAccess()')
console.log('3. If authentication fails, run: emergencyTokenRecovery()')
console.log('4. Check browser network tab for API call status codes')
console.log('5. Look for console errors related to CORS or authentication')

console.log('\n🎯 Expected Behavior for matt.lindop@zebra.associates:')
console.log('   - Should have valid access_token in localStorage or cookies')
console.log('   - User should have role: "admin"')
console.log('   - Admin console should be accessible at /admin')
console.log('   - API calls should include Authorization header')

console.log('\n🔧 Authentication Flow Test Complete')