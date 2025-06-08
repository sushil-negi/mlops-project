#!/usr/bin/env python3
"""
Test runner script for Healthcare AI system
Provides comprehensive testing with coverage reporting
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def install_test_dependencies():
    """Install test dependencies"""
    print("📦 Installing test dependencies...")
    requirements_file = project_root / "tests" / "requirements.txt"
    
    if requirements_file.exists():
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True)
        print("✅ Test dependencies installed")
    else:
        print("⚠️ No test requirements file found")

def run_unit_tests():
    """Run unit tests"""
    print("\n🧪 Running Unit Tests...")
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/unit/",
        "-v",
        "--cov=models/healthcare-ai/src",
        "--cov=scripts",
        "--cov-report=term-missing",
        "-m", "not slow"
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def run_integration_tests():
    """Run integration tests"""
    print("\n🔗 Running Integration Tests...")
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/integration/", 
        "-v",
        "--cov=models/healthcare-ai/src",
        "--cov=scripts",
        "--cov-append",
        "-m", "integration"
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def run_e2e_tests(skip_web=False):
    """Run end-to-end tests"""
    print("\n🌐 Running End-to-End Tests...")
    
    markers = "e2e"
    if skip_web:
        markers += " and not web"
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/e2e/",
        "-v", 
        "--cov=models/healthcare-ai/src",
        "--cov=scripts",
        "--cov-append",
        "-m", markers
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def run_all_tests(skip_web=False, skip_e2e=False):
    """Run all tests with coverage"""
    print("🚀 Running Full Test Suite...")
    
    markers = []
    if skip_web:
        markers.append("not web")
    if skip_e2e:
        markers.append("not e2e")
    
    marker_expr = " and ".join(markers) if markers else ""
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--cov=models/healthcare-ai/src",
        "--cov=scripts", 
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "--cov-report=xml:coverage.xml",
        "--cov-fail-under=80"
    ]
    
    if marker_expr:
        cmd.extend(["-m", marker_expr])
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def generate_coverage_report():
    """Generate detailed coverage report"""
    print("\n📊 Generating Coverage Report...")
    
    # Generate HTML report
    subprocess.run([
        sys.executable, "-m", "coverage", "html",
        "--directory=htmlcov",
        "--title=Healthcare AI Test Coverage"
    ], cwd=project_root)
    
    # Generate XML report for CI/CD
    subprocess.run([
        sys.executable, "-m", "coverage", "xml",
        "-o", "coverage.xml"
    ], cwd=project_root)
    
    # Print coverage summary
    subprocess.run([
        sys.executable, "-m", "coverage", "report"
    ], cwd=project_root)
    
    coverage_html = project_root / "htmlcov" / "index.html"
    if coverage_html.exists():
        print(f"📈 Coverage report available at: file://{coverage_html.absolute()}")

def check_service_health():
    """Check if healthcare API service is running"""
    try:
        import requests
        response = requests.get("http://localhost:8091/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def lint_code():
    """Run code linting"""
    print("\n🔍 Running Code Linting...")
    
    # Try to run flake8 if available
    try:
        subprocess.run([
            sys.executable, "-m", "flake8",
            "models/healthcare-ai/src/",
            "scripts/",
            "--max-line-length=120",
            "--ignore=E501,W503"
        ], cwd=project_root, check=True)
        print("✅ Linting passed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ Linting skipped (flake8 not available)")
        return True

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Healthcare AI Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests") 
    parser.add_argument("--e2e", action="store_true", help="Run only end-to-end tests")
    parser.add_argument("--skip-web", action="store_true", help="Skip web interface tests")
    parser.add_argument("--skip-e2e", action="store_true", help="Skip end-to-end tests")
    parser.add_argument("--no-install", action="store_true", help="Skip dependency installation")
    parser.add_argument("--no-lint", action="store_true", help="Skip code linting")
    parser.add_argument("--coverage-only", action="store_true", help="Only generate coverage report")
    
    args = parser.parse_args()
    
    print("🏥 Healthcare AI Test Suite")
    print("=" * 50)
    
    # Install dependencies
    if not args.no_install:
        try:
            install_test_dependencies()
        except subprocess.CalledProcessError:
            print("❌ Failed to install test dependencies")
            return 1
    
    # Run linting
    if not args.no_lint:
        if not lint_code():
            return 1
    
    # Generate coverage report only
    if args.coverage_only:
        generate_coverage_report()
        return 0
    
    # Check if API service is running for integration/e2e tests
    service_running = check_service_health()
    if not service_running and (args.integration or args.e2e or (not any([args.unit, args.integration, args.e2e]))):
        print("⚠️ Healthcare API service not running on localhost:8091")
        print("   Some integration/e2e tests may fail")
        print("   Start service with: python3 scripts/start_healthcare_ai_service.py")
    
    success = True
    start_time = time.time()
    
    try:
        if args.unit:
            success = run_unit_tests()
        elif args.integration:
            success = run_integration_tests()
        elif args.e2e:
            success = run_e2e_tests(skip_web=args.skip_web)
        else:
            success = run_all_tests(skip_web=args.skip_web, skip_e2e=args.skip_e2e)
        
        # Generate coverage report
        if success:
            generate_coverage_report()
            
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 1
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n{'=' * 50}")
    if success:
        print(f"✅ All tests passed! ({duration:.1f}s)")
        print("📊 Coverage report generated in htmlcov/")
        return 0
    else:
        print(f"❌ Some tests failed ({duration:.1f}s)")
        return 1

if __name__ == "__main__":
    sys.exit(main())