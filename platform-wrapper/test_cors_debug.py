#!/usr/bin/env python3
"""
Debug script to test CORS origins parsing from Railway environment variables
"""
import os
import json

def test_cors_parsing():
    # Test the exact value from Railway
    cors_origins_env = '["http://localhost:3000","http://localhost:3001","https://frontend-5r7ft62po-zebraassociates-projects.vercel.app","https://app.zebra.associates"]'
    
    print(f"Raw CORS_ORIGINS from Railway: {cors_origins_env}")
    
    # Test the parsing logic from config.py
    def assemble_cors_origins(v):
        """Parse CORS_ORIGINS from various formats: JSON array, comma-separated string, or single URL"""
        if isinstance(v, str):
            # Handle empty or whitespace-only strings
            if not v.strip():
                return ["http://localhost:3000"]
                
            if v.startswith("[") and v.endswith("]"):
                # Handle JSON-like format: ["url1","url2"]
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    # Fall back to comma-separated parsing
                    v = v.strip("[]").replace('"', '').replace("'", "")
                    return [i.strip() for i in v.split(",") if i.strip()]
            else:
                # Handle comma-separated format: url1,url2 or single URL
                return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        # Return default if we can't parse
        return ["http://localhost:3000"]
    
    parsed_origins = assemble_cors_origins(cors_origins_env)
    print(f"Parsed CORS origins: {parsed_origins}")
    
    # Check if our custom domain is included
    custom_domain = "https://app.zebra.associates"
    if custom_domain in parsed_origins:
        print(f"✅ Custom domain {custom_domain} is included in CORS origins")
    else:
        print(f"❌ Custom domain {custom_domain} is NOT included in CORS origins")
    
    return parsed_origins

if __name__ == "__main__":
    test_cors_parsing()