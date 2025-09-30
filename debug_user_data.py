#!/usr/bin/env python3
"""
Debug script to create mock user data for testing
"""

# For now, let's create a simple fix that provides fallback user data
# until the full database/auth flow is properly set up

fallback_user_data = {
    "user": {
        "id": "test-user-id",
        "email": "matt.lindop@zebra.associates",
        "first_name": "Matt",
        "last_name": "Lindop",
        "role": "super_admin",
        "organisation_id": "test-org-id",
        "is_active": True,
        "application_access": [
            {"application": "market_edge", "has_access": True},
            {"application": "causal_edge", "has_access": True},
            {"application": "value_edge", "has_access": True}
        ]
    },
    "tenant": {
        "id": "test-org-id",
        "name": "Zebra Associates",
        "industry": "Consulting",
        "subscription_plan": "enterprise"
    },
    "permissions": ["admin:read", "admin:write", "super_admin:all"],
    "session": {
        "authenticated": True,
        "tenant_isolated": True
    }
}

print("Fallback user data for testing:")
import json
print(json.dumps(fallback_user_data, indent=2))