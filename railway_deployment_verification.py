#!/usr/bin/env python3
"""
Railway Deployment Verification Script
Tests if the ECOMSIMPLY backend is properly configured for Railway deployment.
"""

import os
import subprocess
import json
import requests
from pathlib import Path

def check_dockerfile():
    """Check if Dockerfile exists and is properly configured"""
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        return False, "Dockerfile not found at root"
    
    content = dockerfile_path.read_text()
    checks = {
        "python:3.11-slim": "python:3.11-slim" in content,
        "requirements.txt": "backend/requirements.txt" in content,
        "PORT variable": "${PORT" in content or "$PORT" in content,
        "uvicorn command": "uvicorn" in content and "backend.server:app" in content
    }
    
    all_passed = all(checks.values())
    return all_passed, checks

def check_dockerignore():
    """Check if .dockerignore is properly configured"""
    dockerignore_path = Path(".dockerignore")
    if not dockerignore_path.exists():
        return False, ".dockerignore not found"
    
    content = dockerignore_path.read_text()
    essential_ignores = ["frontend/build", "node_modules", "__pycache__", "*.log"]
    missing = [item for item in essential_ignores if item not in content]
    
    return len(missing) == 0, missing

def check_railway_json():
    """Check if railway.json is configured for Docker"""
    railway_path = Path("railway.json")
    if not railway_path.exists():
        return False, "railway.json not found"
    
    try:
        with open(railway_path) as f:
            config = json.load(f)
        
        build_config = config.get("build", {})
        is_dockerfile = build_config.get("builder") == "dockerfile"
        has_dockerfile_path = "dockerfilePath" in build_config
        
        return is_dockerfile and has_dockerfile_path, config
    except Exception as e:
        return False, f"Error reading railway.json: {e}"

def check_backend_structure():
    """Check if backend directory structure is correct"""
    backend_path = Path("backend")
    if not backend_path.exists():
        return False, "backend directory not found"
    
    required_files = ["requirements.txt", "server.py"]
    missing = [f for f in required_files if not (backend_path / f).exists()]
    
    if missing:
        return False, f"Missing files in backend/: {missing}"
    
    # Check requirements.txt has essential packages
    req_content = (backend_path / "requirements.txt").read_text()
    essential_packages = ["fastapi", "uvicorn"]
    missing_packages = [pkg for pkg in essential_packages if pkg not in req_content.lower()]
    
    return len(missing_packages) == 0, missing_packages

def test_local_backend_start():
    """Test if backend can start locally (for 5 seconds)"""
    try:
        # Start backend server in background
        backend_path = Path("backend")
        env = os.environ.copy()
        env["PORT"] = "8001"
        env["PYTHONPATH"] = str(Path.cwd())
        
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "backend.server:app", "--host", "127.0.0.1", "--port", "8001"],
            cwd=backend_path.parent,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit for server to start
        import time
        time.sleep(3)
        
        # Test health endpoint
        try:
            response = requests.get("http://127.0.0.1:8001/api/health", timeout=2)
            server_works = response.status_code == 200
        except:
            server_works = False
        
        # Kill the process
        process.terminate()
        process.wait(timeout=5)
        
        return server_works, "Backend server starts and responds to health check"
    
    except Exception as e:
        return False, f"Error testing backend: {e}"

def main():
    """Run all verification checks"""
    print("🚀 RAILWAY DEPLOYMENT VERIFICATION")
    print("=" * 50)
    
    # Check 1: Dockerfile
    dockerfile_ok, dockerfile_info = check_dockerfile()
    if dockerfile_ok:
        print("✅ Dockerfile: PASSED")
    else:
        print(f"❌ Dockerfile: FAILED - {dockerfile_info}")
    
    # Check 2: .dockerignore
    dockerignore_ok, dockerignore_info = check_dockerignore()
    if dockerignore_ok:
        print("✅ .dockerignore: PASSED")
    else:
        print(f"❌ .dockerignore: FAILED - Missing: {dockerignore_info}")
    
    # Check 3: railway.json
    railway_ok, railway_info = check_railway_json()
    if railway_ok:
        print("✅ railway.json: PASSED - Docker configuration detected")
    else:
        print(f"❌ railway.json: FAILED - {railway_info}")
    
    # Check 4: Backend structure
    backend_ok, backend_info = check_backend_structure()
    if backend_ok:
        print("✅ Backend Structure: PASSED")
    else:
        print(f"❌ Backend Structure: FAILED - {backend_info}")
    
    # Check 5: Backend can start locally
    print("\n🔄 Testing backend startup...")
    server_ok, server_info = test_local_backend_start()
    if server_ok:
        print("✅ Backend Startup: PASSED - Server responds to health check")
    else:
        print(f"❌ Backend Startup: FAILED - {server_info}")
    
    # Summary
    all_checks = [dockerfile_ok, dockerignore_ok, railway_ok, backend_ok, server_ok]
    passed = sum(all_checks)
    total = len(all_checks)
    
    print(f"\n📊 SUMMARY: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 ALL CHECKS PASSED - Ready for Railway deployment!")
        return True
    else:
        print("⚠️ Some checks failed - Fix issues before deploying to Railway")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)