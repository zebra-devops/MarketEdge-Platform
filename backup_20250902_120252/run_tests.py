#!/usr/bin/env python3
"""
Test runner script for the Platform Wrapper data abstraction layer.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit            # Run only unit tests
    python run_tests.py --integration     # Run only integration tests
    python run_tests.py --coverage        # Run tests with coverage report
    python run_tests.py --verbose         # Run tests with verbose output
    python run_tests.py --help            # Show help
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Please install pytest: pip install pytest pytest-asyncio")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test runner for Platform Wrapper data abstraction layer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit            # Run only unit tests
  python run_tests.py --integration     # Run only integration tests
  python run_tests.py --coverage        # Run tests with coverage report
  python run_tests.py --verbose         # Run tests with verbose output
  python run_tests.py --fast            # Run tests quickly (no coverage)
        """
    )
    
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )
    
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Run tests with verbose output"
    )
    
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run tests quickly (no coverage, minimal output)"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies"
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path("tests").exists():
        print("❌ Error: tests directory not found. Please run this script from the backend directory.")
        sys.exit(1)
    
    # Install dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        deps = [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "pytest-mock"
        ]
        cmd = [sys.executable, "-m", "pip", "install"] + deps
        if not run_command(cmd, "Installing test dependencies"):
            sys.exit(1)
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test selection
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend([
            "--cov=app.data",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-fail-under=80"
        ])
    
    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    elif args.fast:
        cmd.extend(["-q", "--tb=no"])
    
    # Run the tests
    success = run_command(cmd, "Running tests")
    
    if success:
        print("\n✅ All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 