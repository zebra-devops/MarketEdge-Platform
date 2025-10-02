"""Test script to reproduce the rate limiter decorator issue"""
import asyncio
from functools import wraps
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

app = FastAPI()

# Simulate the rate limiter decorator
def rate_limit_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract request
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        if not request and 'request' in kwargs:
            request = kwargs['request']

        print(f"Decorator wrapper called with args={args}, kwargs={kwargs}")

        # Call original function
        return await func(*args, **kwargs)

    return wrapper

# Test endpoint WITHOUT decorator
@app.get("/test-without-decorator")
async def test_without(request: Request, redirect_uri: str):
    return {"message": "success", "redirect_uri": redirect_uri}

# Test endpoint WITH decorator
@app.get("/test-with-decorator")
@rate_limit_decorator
async def test_with(request: Request, redirect_uri: str):
    return {"message": "success", "redirect_uri": redirect_uri}

if __name__ == "__main__":
    client = TestClient(app)

    print("\n=== Testing WITHOUT decorator ===")
    response = client.get("/test-without-decorator?redirect_uri=http://localhost:3000/callback")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    print("\n=== Testing WITH decorator ===")
    response = client.get("/test-with-decorator?redirect_uri=http://localhost:3000/callback")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    else:
        print(f"Error: {response.json()}")

    # Check OpenAPI schema
    print("\n=== OpenAPI Schema ===")
    schema = client.get("/openapi.json").json()

    print("\nWithout decorator endpoint:")
    without_params = schema['paths']['/test-without-decorator']['get'].get('parameters', [])
    for param in without_params:
        print(f"  - {param['name']}: required={param.get('required', False)}")

    print("\nWith decorator endpoint:")
    with_params = schema['paths']['/test-with-decorator']['get'].get('parameters', [])
    for param in with_params:
        print(f"  - {param['name']}: required={param.get('required', False)}")
