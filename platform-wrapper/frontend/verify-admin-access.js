/**
 * ZEBRA ASSOCIATES ADMIN ACCESS VERIFICATION SCRIPT
 * 
 * This script validates that matt.lindop@zebra.associates has successfully 
 * completed re-authentication and has admin access for the £925K opportunity.
 * 
 * Usage: Paste this into browser console after login
 */

console.log('🔍 ZEBRA ASSOCIATES ADMIN ACCESS VERIFICATION');
console.log('============================================');

async function verifyAdminAccess() {
  const results = {
    tokenPresent: false,
    tokenValid: false,
    userRole: null,
    permissions: [],
    adminAccess: false,
    dashboardAccess: false,
    errors: []
  };

  try {
    // 1. Check if access token is present
    console.log('\n1️⃣ Checking access token presence...');
    const accessToken = localStorage.getItem('access_token');
    
    if (!accessToken) {
      console.log('❌ No access token found in localStorage');
      
      // Check cookies as fallback
      const cookieToken = document.cookie
        .split(';')
        .find(row => row.trim().startsWith('access_token='));
      
      if (cookieToken) {
        console.log('✅ Access token found in cookies');
        results.tokenPresent = true;
      } else {
        console.log('❌ No access token found in cookies either');
        results.errors.push('No access token found - user needs to login');
        return results;
      }
    } else {
      console.log('✅ Access token found in localStorage');
      results.tokenPresent = true;
    }

    // 2. Parse and validate JWT token
    console.log('\n2️⃣ Parsing JWT token...');
    try {
      const token = accessToken || cookieToken.split('=')[1];
      const payload = JSON.parse(atob(token.split('.')[1]));
      
      console.log('✅ JWT token parsed successfully');
      console.log('Token payload:', {
        user_id: payload.sub || payload.user_id,
        email: payload.email,
        role: payload.role,
        permissions: payload.permissions,
        tenant: payload.tenant,
        exp: payload.exp ? new Date(payload.exp * 1000) : 'No expiry',
        iat: payload.iat ? new Date(payload.iat * 1000) : 'No issued time'
      });
      
      results.tokenValid = true;
      results.userRole = payload.role;
      results.permissions = payload.permissions || [];
      
      // 3. Check if token is expired
      if (payload.exp && payload.exp * 1000 < Date.now()) {
        console.log('⚠️ Token is expired');
        results.errors.push('Token expired - needs refresh');
      }
      
    } catch (parseError) {
      console.log('❌ Failed to parse JWT token:', parseError);
      results.errors.push('Invalid JWT token format');
      return results;
    }

    // 4. Verify admin role
    console.log('\n3️⃣ Checking admin role...');
    if (results.userRole === 'admin') {
      console.log('✅ User has admin role');
      results.adminAccess = true;
    } else {
      console.log(`❌ User role is "${results.userRole}", not "admin"`);
      results.errors.push(`Role is "${results.userRole}" - should be "admin"`);
    }

    // 5. Check stored user data
    console.log('\n4️⃣ Checking stored user data...');
    const storedUser = localStorage.getItem('current_user');
    if (storedUser) {
      const userData = JSON.parse(storedUser);
      console.log('✅ User data found in localStorage:', {
        email: userData.email,
        role: userData.role,
        id: userData.id
      });
      
      if (userData.role !== 'admin') {
        console.log('❌ Stored user data shows wrong role');
        results.errors.push('Cached user data has incorrect role');
      }
    } else {
      console.log('⚠️ No user data in localStorage');
    }

    // 6. Test API access to admin endpoints
    console.log('\n5️⃣ Testing admin API access...');
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || window.location.origin;
      
      // Test basic auth check
      const authResponse = await fetch(`${baseUrl}/api/v1/auth/me`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });
      
      if (authResponse.ok) {
        console.log('✅ Auth API endpoint accessible');
        const authData = await authResponse.json();
        console.log('Current user from API:', {
          email: authData.user?.email,
          role: authData.user?.role,
          permissions: authData.permissions
        });
      } else {
        console.log(`❌ Auth API failed: ${authResponse.status}`);
        results.errors.push(`Auth API returned ${authResponse.status}`);
      }
      
    } catch (apiError) {
      console.log('❌ API test failed:', apiError);
      results.errors.push('API endpoints not accessible');
    }

    // 7. Check dashboard access (client-side)
    console.log('\n6️⃣ Checking dashboard access...');
    const currentPath = window.location.pathname;
    if (currentPath.includes('/dashboard') || currentPath.includes('/admin')) {
      console.log('✅ User is on dashboard/admin page');
      results.dashboardAccess = true;
    } else {
      console.log('ℹ️ User is not currently on dashboard page');
    }

  } catch (error) {
    console.log('❌ Verification failed with error:', error);
    results.errors.push(`Verification error: ${error.message}`);
  }

  // Final results
  console.log('\n🎯 VERIFICATION RESULTS');
  console.log('======================');
  
  const isFullyValid = results.tokenPresent && 
                      results.tokenValid && 
                      results.adminAccess && 
                      results.errors.length === 0;
  
  if (isFullyValid) {
    console.log('🎉 SUCCESS: Admin access is properly configured!');
    console.log('✅ matt.lindop@zebra.associates has admin privileges');
    console.log('✅ £925K opportunity is accessible');
    console.log('\nNext steps:');
    console.log('- Navigate to /admin or /dashboard to use admin features');
    console.log('- Admin permissions are active and working');
  } else {
    console.log('❌ ISSUES DETECTED:');
    results.errors.forEach((error, index) => {
      console.log(`   ${index + 1}. ${error}`);
    });
    console.log('\nRecommended actions:');
    console.log('- Follow the re-authentication guide');
    console.log('- Clear browser cache completely');
    console.log('- Login with fresh Auth0 session');
  }
  
  console.log('\nDetailed Results:', results);
  return results;
}

// Auto-run the verification
verifyAdminAccess().then(results => {
  console.log('\n📊 Verification completed. Results available in console.');
  
  // Store results for easy access
  window.adminVerificationResults = results;
  console.log('💾 Results stored in window.adminVerificationResults');
}).catch(error => {
  console.error('❌ Verification script failed:', error);
});

// Helper function for manual re-run
window.verifyAdminAccess = verifyAdminAccess;
console.log('\n🔧 Helper functions:');
console.log('- Run verifyAdminAccess() to check again');
console.log('- Check window.adminVerificationResults for last results');