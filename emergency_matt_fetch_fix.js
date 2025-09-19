/**
 * EMERGENCY FIX for Matt Lindop's "Invalid value" fetch error
 * Run this in browser console IMMEDIATELY
 */

console.log('🚨 EMERGENCY FETCH FIX for Matt Lindop - £925K Zebra Associates deal')

// IMMEDIATE FIX: Create a safe test function that bypasses problematic axios interceptor
window.emergencyAdminTest = async function() {
  console.log('\n🔧 EMERGENCY: Testing admin access without axios interceptors...')

  // Get token safely
  let token = null
  try {
    // Try cookies first
    const cookies = document.cookie.split(';')
    const tokenCookie = cookies.find(c => c.trim().startsWith('access_token='))
    if (tokenCookie) {
      token = tokenCookie.split('=')[1]
      console.log('✅ Token found in cookies')
    }

    // Fallback to localStorage
    if (!token) {
      token = localStorage.getItem('access_token')
      if (token) {
        console.log('✅ Token found in localStorage')
      }
    }

    if (!token) {
      console.log('❌ No token found - user needs to log in')
      return { success: false, error: 'No token found' }
    }

    // Validate token format
    const cleanToken = token.trim().replace(/[\n\r\t]/g, '')
    if (!cleanToken) {
      console.log('❌ Token is empty after cleaning')
      return { success: false, error: 'Empty token' }
    }

    if (!/^[A-Za-z0-9\-._~+/]+=*$/.test(cleanToken)) {
      console.log('❌ Token contains invalid characters')
      console.log('Token preview:', cleanToken.substring(0, 50))
      return { success: false, error: 'Invalid token format' }
    }

    console.log('✅ Token format is valid')

  } catch (tokenError) {
    console.error('❌ Token retrieval failed:', tokenError)
    return { success: false, error: `Token error: ${tokenError.message}` }
  }

  // Test with raw fetch to bypass axios issues
  const baseUrl = process?.env?.NEXT_PUBLIC_API_BASE_URL || 'https://marketedge-platform.onrender.com'
  const url = `${baseUrl}/api/v1/admin/feature-flags`

  console.log(`🌐 Testing: ${url}`)

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${cleanToken}`
      }
    })

    console.log(`📊 Response: ${response.status} ${response.statusText}`)

    if (response.ok) {
      console.log('✅ SUCCESS: Admin API access working!')
      const data = await response.json()
      console.log('Admin data:', data)
      return { success: true, data }
    } else {
      const errorText = await response.text()
      console.log('❌ Admin access denied:', errorText)
      return { success: false, error: `${response.status}: ${errorText}` }
    }

  } catch (fetchError) {
    console.error('❌ Raw fetch failed:', fetchError)
    console.error('Error type:', fetchError.constructor.name)
    console.error('Error message:', fetchError.message)

    // This is the specific error Matt is seeing
    if (fetchError.message.includes('Invalid value')) {
      console.log('\n🎯 FOUND THE ISSUE: "Invalid value" fetch error')
      console.log('💡 SOLUTION: Token or header contains invalid characters')
      console.log('🔧 FIX: Check token format and axios interceptor header validation')
    }

    return { success: false, error: `Fetch error: ${fetchError.message}` }
  }
}

// IMMEDIATE FIX: Create bypass version of testAdminApiAccess
window.safeTestAdminApiAccess = async function() {
  console.log('\n🛡️ SAFE VERSION: Testing admin API access with enhanced error handling...')

  try {
    const result = await window.emergencyAdminTest()

    if (result.success) {
      console.log('✅ ADMIN ACCESS CONFIRMED - Matt can access admin features')
      return result
    } else {
      console.log('❌ ADMIN ACCESS BLOCKED:', result.error)

      // Provide specific troubleshooting based on error
      if (result.error.includes('No token')) {
        console.log('\n🔧 SOLUTION: Matt needs to log in again')
        console.log('   1. Go to login page')
        console.log('   2. Authenticate with matt.lindop@zebra.associates')
        console.log('   3. Ensure super_admin role is assigned')
      } else if (result.error.includes('Invalid token')) {
        console.log('\n🔧 SOLUTION: Token format issue detected')
        console.log('   1. Clear browser storage: localStorage.clear()')
        console.log('   2. Clear cookies and re-login')
        console.log('   3. Check for special characters in token')
      } else if (result.error.includes('403')) {
        console.log('\n🔧 SOLUTION: Permission issue')
        console.log('   1. Verify super_admin role in backend')
        console.log('   2. Check user permissions in database')
        console.log('   3. Confirm organization context')
      } else if (result.error.includes('Invalid value')) {
        console.log('\n🔧 SOLUTION: This is the axios interceptor bug!')
        console.log('   1. Token contains invalid characters')
        console.log('   2. Header validation failed')
        console.log('   3. Use this safe function instead of testAdminApiAccess()')
      }

      return result
    }
  } catch (error) {
    console.error('🚨 EMERGENCY FUNCTION FAILED:', error)
    return { success: false, error: `Emergency test failed: ${error.message}` }
  }
}

// Auto-run the safe test
console.log('\n🚀 RUNNING EMERGENCY TEST NOW...')
window.safeTestAdminApiAccess().then(result => {
  console.log('\n🎯 EMERGENCY TEST COMPLETE')

  if (result.success) {
    console.log('✅ MATT CAN ACCESS ADMIN FEATURES')
    console.log('✅ ZEBRA ASSOCIATES £925K DEAL IS SECURE')
    console.log('\n🎉 Use safeTestAdminApiAccess() instead of testAdminApiAccess()')
  } else {
    console.log('❌ ADMIN ACCESS STILL BLOCKED')
    console.log('❌ IMMEDIATE DEVELOPER INTERVENTION REQUIRED')
    console.log('\n📞 ESCALATE TO DEVELOPMENT TEAM IMMEDIATELY')
  }
}).catch(error => {
  console.error('🚨 CRITICAL FAILURE:', error)
  console.log('📞 ESCALATE TO SENIOR DEVELOPER IMMEDIATELY')
})

console.log('\n🔧 NEW FUNCTIONS AVAILABLE:')
console.log('   - emergencyAdminTest() - Raw fetch test bypassing axios')
console.log('   - safeTestAdminApiAccess() - Safe replacement for testAdminApiAccess()')
console.log('\n💡 USE safeTestAdminApiAccess() INSTEAD OF testAdminApiAccess()')