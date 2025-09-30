#!/usr/bin/env python3
"""
Test the /me endpoint with Matt's JWT token to see what user data is being returned
"""
import requests

# Your JWT token from the browser dev tools
jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmOTZlZDJmYi0wYzU4LTQ0NWEtODU1YS1lMGQ2NmY1NmZiY2YiLCJ0ZW5hbnRfaWQiOiI4MzVkNGYyNC1jZmYyLTQzZTgtYTQ3MC05MzIxNmEzZDk5YTMiLCJyb2xlIjoic3VwZXJfYWRtaW4iLCJleHAiOjE3NTg2NDUwNzYsImlhdCI6MTc1ODY0MzI3NiwidHlwZSI6ImFjY2VzcyIsImp0aSI6IjZIZGd1YlJkNHJSYlN3TFdHWkRQS0EiLCJpc3MiOiJtYXJrZXQtZWRnZS1wbGF0Zm9ybSIsImF1ZCI6Im1hcmtldC1lZGdlLWFwaSJ9.T5BNZGeuVWHjePuVAwwUh3tlN1E98IT-X9NAEKkUnhk"

print("=== TESTING /me ENDPOINT ===")

# Test the /me endpoint
try:
    response = requests.get(
        "http://localhost:8000/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/json"
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")

    if response.status_code == 200:
        user_data = response.json()
        print("✅ SUCCESS - User data returned:")
        print(f"  Email: {user_data.get('email', 'N/A')}")
        print(f"  Role: {user_data.get('role', 'N/A')}")
        print(f"  Organisation: {user_data.get('organisation', {}).get('name', 'N/A')}")
        print(f"  Is Active: {user_data.get('is_active', 'N/A')}")
        print(f"  Full response: {user_data}")
    else:
        print(f"❌ ERROR: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"❌ Request failed: {e}")

# Also test admin endpoints
print("\n=== TESTING ADMIN ENDPOINTS ===")

endpoints_to_test = [
    "/api/v1/admin/users",
    "/api/v1/admin/organisations",
    "/api/v1/admin/dashboard/stats"
]

for endpoint in endpoints_to_test:
    try:
        response = requests.get(
            f"http://localhost:8000{endpoint}",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/json"
            }
        )
        print(f"{endpoint}: {response.status_code}")
        if response.status_code != 200:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"{endpoint}: Request failed - {e}")