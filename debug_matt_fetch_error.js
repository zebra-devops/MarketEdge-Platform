/**
 * EMERGENCY: Debug Matt Lindop's fetch error
 * Run this in browser console to diagnose the "Invalid value" fetch error
 */

console.log('🚨 EMERGENCY: Debugging Matt Lindop fetch error...')

// 1. Check environment variables
console.log('\n📊 Environment Check:')
console.log('NEXT_PUBLIC_API_BASE_URL:', process?.env?.NEXT_PUBLIC_API_BASE_URL || window?.location?.origin || 'UNDEFINED')
console.log('NODE_ENV:', process?.env?.NODE_ENV || 'UNDEFINED')

// 2. Check token status and format
console.log('\n🔐 Token Analysis:')

function analyzeToken(token, source) {
  if (!token) {
    console.log(`${source}: ❌ NO TOKEN`)
    return false
  }

  console.log(`${source}: ✅ FOUND`)
  console.log(`  Length: ${token.length}`)
  console.log(`  Preview: ${token.substring(0, 20)}...`)
  console.log(`  Contains newlines: ${token.includes('\n') ? '❌ YES' : '✅ NO'}`)
  console.log(`  Contains nulls: ${token.includes('\0') ? '❌ YES' : '✅ NO'}`)
  console.log(`  Valid Bearer format: ${/^[A-Za-z0-9\-._~+/]+=*$/.test(token) ? '✅ YES' : '❌ NO'}`)

  return true
}

// Check tokens from all sources
const cookieToken = document.cookie.split(';').find(c => c.trim().startsWith('access_token='))?.split('=')[1]
const localStorageToken = localStorage.getItem('access_token')

analyzeToken(cookieToken, 'Cookie Token')
analyzeToken(localStorageToken, 'LocalStorage Token')

// 3. Test basic fetch without axios
console.log('\n🌐 Raw Fetch Test:')

async function testRawFetch() {
  const baseUrl = process?.env?.NEXT_PUBLIC_API_BASE_URL || 'https://marketedge-platform.onrender.com'
  const token = cookieToken || localStorageToken

  console.log(`Testing: ${baseUrl}/api/v1/health`)

  try {
    const response = await fetch(`${baseUrl}/api/v1/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      }
    })

    console.log('✅ Raw fetch successful:', response.status, response.statusText)
    const data = await response.text()
    console.log('Response:', data.substring(0, 200))

    return true
  } catch (error) {
    console.error('❌ Raw fetch failed:', error)
    console.error('Error type:', error.constructor.name)
    console.error('Error message:', error.message)

    return false
  }
}

// 4. Test admin endpoint with raw fetch
async function testAdminRawFetch() {
  const baseUrl = process?.env?.NEXT_PUBLIC_API_BASE_URL || 'https://marketedge-platform.onrender.com'
  const token = cookieToken || localStorageToken

  if (!token) {
    console.log('❌ Cannot test admin endpoint - no token found')
    return false
  }

  console.log(`Testing admin: ${baseUrl}/api/v1/admin/feature-flags`)

  try {
    const response = await fetch(`${baseUrl}/api/v1/admin/feature-flags`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    })

    console.log('✅ Admin raw fetch status:', response.status, response.statusText)

    if (response.ok) {
      console.log('✅ Admin access working!')
    } else {
      console.log('❌ Admin access denied:', await response.text())
    }

    return response.ok
  } catch (error) {
    console.error('❌ Admin raw fetch failed:', error)
    return false
  }
}

// 5. Check axios configuration
console.log('\n⚙️ Axios Configuration Check:')

function checkAxiosConfig() {
  try {
    // Try to access the apiService
    if (window.apiService) {
      console.log('✅ ApiService available on window')
    } else {
      console.log('❌ ApiService not available on window')
    }

    // Check axios defaults
    if (window.axios) {
      console.log('✅ Axios available globally')
      console.log('Axios defaults:', {
        baseURL: window.axios.defaults.baseURL,
        timeout: window.axios.defaults.timeout,
        headers: Object.keys(window.axios.defaults.headers || {})
      })
    } else {
      console.log('❌ Axios not available globally')
    }

  } catch (error) {
    console.error('❌ Axios config check failed:', error)
  }
}

checkAxiosConfig()

// Run all tests
console.log('\n🏃 Running All Tests...')

async function runAllTests() {
  console.log('\n1️⃣ Testing raw health endpoint...')
  const healthTest = await testRawFetch()

  console.log('\n2️⃣ Testing raw admin endpoint...')
  const adminTest = await testAdminRawFetch()

  console.log('\n📋 SUMMARY:')
  console.log(`Health endpoint: ${healthTest ? '✅ WORKING' : '❌ FAILED'}`)
  console.log(`Admin endpoint: ${adminTest ? '✅ WORKING' : '❌ FAILED'}`)

  if (healthTest && !adminTest) {
    console.log('\n💡 DIAGNOSIS: Network works, likely auth/permissions issue')
  } else if (!healthTest) {
    console.log('\n💡 DIAGNOSIS: Network/URL issue - check base URL and CORS')
  }

  return { healthTest, adminTest }
}

// Auto-run the tests
runAllTests().then(result => {
  console.log('\n✅ Diagnostic complete!')

  if (!result.healthTest) {
    console.log('\n🔧 IMMEDIATE FIX NEEDED:')
    console.log('1. Check NEXT_PUBLIC_API_BASE_URL environment variable')
    console.log('2. Verify backend server is running')
    console.log('3. Check CORS configuration')
  } else if (!result.adminTest) {
    console.log('\n🔧 IMMEDIATE FIX NEEDED:')
    console.log('1. Check token validity with debugAuthState()')
    console.log('2. Verify admin role in backend')
    console.log('3. Check token format and encoding')
  }
}).catch(error => {
  console.error('❌ Diagnostic script failed:', error)
})

console.log('\n🎯 Copy and paste this entire script into browser console')