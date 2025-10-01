// Debug frontend storage to see what user data is cached
// Run this in browser console on the user management page

console.log('🔍 DEBUGGING FRONTEND STORAGE FOR matt.lindop@zebra.associates');
console.log('=' .repeat(70));

// 1. Check localStorage
console.log('1. LOCALSTORAGE DATA:');
const localUser = localStorage.getItem('current_user');
if (localUser) {
    const userData = JSON.parse(localUser);
    console.log('   ✅ User found in localStorage:');
    console.log('   📧 Email:', userData.email);
    console.log('   🎭 Role:', userData.role);
    console.log('   🏢 Organization:', userData.organisation_id);
    console.log('   📱 App Access:', userData.application_access || 'None in localStorage');
} else {
    console.log('   ❌ No user data in localStorage');
}

// 2. Check sessionStorage
console.log('\n2. SESSIONSTORAGE DATA:');
const sessionKeys = Object.keys(sessionStorage);
const authSession = sessionKeys.find(key => key.includes('auth'));
if (authSession) {
    const sessionData = JSON.parse(sessionStorage.getItem(authSession));
    console.log('   ✅ Auth session found:', authSession);
    if (sessionData.user) {
        console.log('   📧 Email:', sessionData.user.email);
        console.log('   🎭 Role:', sessionData.user.role);
        console.log('   🏢 Organization:', sessionData.user.organisation_id);
        console.log('   📱 App Access:', sessionData.user.application_access || 'None in session');
    }
} else {
    console.log('   ❌ No auth session in sessionStorage');
}

// 3. Check tenant info
console.log('\n3. TENANT INFO:');
const tenantInfo = localStorage.getItem('tenant_info');
if (tenantInfo) {
    const tenant = JSON.parse(tenantInfo);
    console.log('   ✅ Tenant found:', tenant.name);
    console.log('   🏭 Industry:', tenant.industry);
    console.log('   📋 Plan:', tenant.subscription_plan);
} else {
    console.log('   ❌ No tenant info in localStorage');
}

// 4. Check permissions
console.log('\n4. PERMISSIONS:');
const permissions = localStorage.getItem('user_permissions');
if (permissions) {
    const perms = JSON.parse(permissions);
    console.log('   ✅ Permissions found:', perms.length, 'permissions');
    console.log('   📝 List:', perms);
} else {
    console.log('   ❌ No permissions in localStorage');
}

// 5. Check cookies (access_token availability)
console.log('\n5. COOKIES:');
const hasAccessToken = document.cookie.includes('access_token=');
const hasRefreshToken = document.cookie.includes('refresh_token=');
console.log('   🍪 Access Token Cookie:', hasAccessToken ? '✅ Present' : '❌ Missing');
console.log('   🍪 Refresh Token Cookie:', hasRefreshToken ? '✅ Present' : '❌ Missing');

// 6. Check React state (if available)
console.log('\n6. REACT STATE:');
console.log('   ℹ️  Open React DevTools to inspect:');
console.log('   - OrganisationProvider isSuperAdmin state');
console.log('   - AuthContext user state');
console.log('   - OrganizationUserManagement component state');

console.log('\n🔍 DEBUGGING COMPLETE - Check above for inconsistencies');
console.log('💡 TIP: Compare this data with what the user management UI shows');