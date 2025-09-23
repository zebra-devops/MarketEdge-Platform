#!/usr/bin/env python3
"""
Debug Production Import Issues

This script will help diagnose what's happening with the production imports
by creating a debug endpoint that shows the actual file contents.
"""

from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
import os
import inspect
import sys

debug_router = APIRouter()

@debug_router.get("/debug/production-imports")
async def debug_production_imports():
    """Debug endpoint to show production file contents and import paths"""
    debug_info = {
        "python_version": sys.version,
        "python_path": sys.path,
        "working_directory": os.getcwd(),
        "files": {}
    }

    # Check if __init__.py exists and its contents
    init_file_path = "/app/app/api/api_v1/endpoints/__init__.py"

    try:
        if os.path.exists(init_file_path):
            with open(init_file_path, 'r') as f:
                debug_info["files"]["init_py_content"] = f.read()
        else:
            debug_info["files"]["init_py_content"] = "FILE_NOT_FOUND"
    except Exception as e:
        debug_info["files"]["init_py_error"] = str(e)

    # Check directory contents
    try:
        endpoints_dir = "/app/app/api/api_v1/endpoints"
        if os.path.exists(endpoints_dir):
            debug_info["files"]["endpoints_directory"] = os.listdir(endpoints_dir)
        else:
            debug_info["files"]["endpoints_directory"] = "DIRECTORY_NOT_FOUND"
    except Exception as e:
        debug_info["files"]["directory_error"] = str(e)

    # Check for broken_endpoint file
    broken_endpoint_path = "/app/app/api/api_v1/endpoints/broken_endpoint.py"
    debug_info["files"]["broken_endpoint_exists"] = os.path.exists(broken_endpoint_path)

    return JSONResponse(debug_info)

# This can be added to the main app for debugging
if __name__ == "__main__":
    print("Debug router created. Add to main app with:")
    print("app.include_router(debug_router, prefix='/api/v1')")