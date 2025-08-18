# How to Get a Valid Auth0 Code for Testing

## The Problem
Our current tests use **fake Auth0 codes** that only test the **400 error path** (invalid codes). The frontend is experiencing **500 errors** with **real Auth0 codes**, but we're not reproducing this because we're testing the wrong scenario.

## Step-by-Step Instructions

### Method 1: Extract from Browser Network Tab (Recommended)

1. **Open Frontend App**
   ```bash
   # Make sure frontend is running
   cd /Users/matt/Sites/MarketEdge/platform-wrapper/frontend
   npm start
   ```

2. **Open Browser Developer Tools**
   - Go to `http://localhost:3000`
   - Press `F12` (or `Cmd+Option+I` on Mac)
   - Go to **Network** tab
   - Check "Preserve log" option

3. **Clear Network Tab**
   - Click the clear button (🚫) in Network tab
   - This ensures you only see the login request

4. **Attempt Login**
   - Click the login button in your app
   - You'll get redirected to Auth0
   - Complete the Auth0 login process
   - You'll be redirected back with a code parameter

5. **Extract the Auth0 Code**
   - In the Network tab, look for a POST request to `/api/v1/auth/login`
   - Click on this request
   - Go to the **Request** tab or **Payload** tab
   - Copy the `code` value (it will be 50+ characters long)
   
   Example:
   ```json
   {
     "code": "j7XwdVpBc8E7nqbNxj3X2YL9vKL3E4dPqT7Y2X4B9c6FvP8Q1m7HwP3Z9",
     "redirect_uri": "http://localhost:3000/callback",
     "state": "abc123"
   }
   ```

6. **Test Immediately**
   ```bash
   cd /Users/matt/Sites/MarketEdge/platform-wrapper/backend
   python test_valid_auth_code.py "j7XwdVpBc8E7nqbNxj3X2YL9vKL3E4dPqT7Y2X4B9c6FvP8Q1m7HwP3Z9"
   ```

   **IMPORTANT**: Auth0 codes expire in ~10 minutes, so run the test immediately!

### Method 2: Programmatic Code Generation

If you can't use the browser method, here's a script approach:

```python
# Will create this if needed - generates valid codes programmatically
python generate_valid_auth0_code.py
```

## Expected Results

### With Invalid/Fake Codes (Current Tests)
```
✅ 400 Bad Request - "Invalid authorization code"
❌ This only tests the failure path
```

### With Valid Auth0 Codes (What We Need)
```
❌ 500 Internal Server Error - Backend crashes
✅ This tests the success path where the real error occurs
```

## What the Valid Code Test Will Reveal

When you run the test with a real Auth0 code, you'll likely see a **500 error** and the backend logs will show the **exact stack trace** of where the crash occurs. This could be:

1. **User Info Retrieval Error** (lines 188-212 in auth.py)
2. **Database Error** (lines 250-298 in auth.py)
3. **JWT Token Creation Error** (lines 310-327 in auth.py)
4. **Response Assembly Error** (lines 372-393 in auth.py)

## Next Steps After Getting the 500 Error

1. **Check Backend Logs**
   ```bash
   tail -f /Users/matt/Sites/MarketEdge/platform-wrapper/backend/server.log
   ```

2. **Look for the Stack Trace**
   - Find the detailed traceback showing exactly which line crashed
   - This will tell us the root cause (database connection, missing config, etc.)

3. **Fix the Root Cause**
   - Based on the stack trace, fix the specific issue
   - Common issues: database not initialized, missing environment variables, Auth0 config problems

4. **Retest**
   - Use the same valid Auth0 code (if it hasn't expired)
   - Verify the fix works

## Why This Approach is Critical

The user is absolutely right - **we've been testing the wrong code path**:

- **❌ Our Tests**: Invalid codes → 400 error (not the real problem)
- **✅ Reality**: Valid codes → 500 error (the actual frontend experience)

This is a fundamental testing methodology issue that we need to fix to properly diagnose and resolve the authentication problems.