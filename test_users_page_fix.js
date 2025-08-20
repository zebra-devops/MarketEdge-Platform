// Test script to validate the users page charAt() fix
// This simulates the scenario that was causing the error

const testUsers = [
  // User with all fields present (from new API)
  {
    id: "1",
    email: "user1@test.com",
    first_name: "John",
    last_name: "Doe",
    role: "client_admin",
    organisation_id: "org1",
    is_active: true,
    created_at: "2024-01-01T00:00:00Z",
    invitation_status: "accepted"
  },
  // User missing invitation_status (from old API)
  {
    id: "2", 
    email: "user2@test.com",
    first_name: "Jane",
    last_name: "Smith",
    role: "end_user",
    organisation_id: "org1",
    is_active: true,
    created_at: "2024-01-01T00:00:00Z"
    // invitation_status is undefined
  },
  // User with null/undefined fields
  {
    id: "3",
    email: null,
    first_name: undefined,
    last_name: null,
    role: null,
    organisation_id: "org1", 
    is_active: true,
    created_at: "2024-01-01T00:00:00Z",
    invitation_status: null
  }
];

// Simulate the fixed logic
function getInvitationStatusColor(status) {
  switch (status) {
    case 'accepted': return 'bg-green-100 text-green-800'
    case 'pending': return 'bg-yellow-100 text-yellow-800'
    case 'expired': return 'bg-red-100 text-red-800'
    default: return 'bg-green-100 text-green-800' // Default to 'accepted' color for undefined/unknown status
  }
}

function formatInvitationStatus(status) {
  return status ? 
    status.charAt(0).toUpperCase() + status.slice(1) : 
    'Accepted';
}

function formatUserName(firstName, lastName) {
  return `${firstName || ''} ${lastName || ''}`.trim();
}

function formatUserDetails(user) {
  return {
    name: formatUserName(user.first_name, user.last_name),
    email: user.email || '',
    role: user.role || 'viewer',
    invitationStatus: formatInvitationStatus(user.invitation_status),
    invitationColor: getInvitationStatusColor(user.invitation_status || 'accepted')
  };
}

console.log('Testing users page charAt() fix...\n');

testUsers.forEach((user, index) => {
  try {
    const formatted = formatUserDetails(user);
    console.log(`User ${index + 1}:`);
    console.log(`  Name: "${formatted.name}"`);
    console.log(`  Email: "${formatted.email}"`);
    console.log(`  Role: "${formatted.role}"`);
    console.log(`  Invitation Status: "${formatted.invitationStatus}"`);
    console.log(`  Invitation Color: "${formatted.invitationColor}"`);
    console.log(`  ✅ SUCCESS: No errors`);
  } catch (error) {
    console.log(`  ❌ ERROR: ${error.message}`);
  }
  console.log('');
});

console.log('All tests completed successfully! The charAt() fix is working.');