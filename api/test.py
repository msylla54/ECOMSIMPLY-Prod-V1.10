#!/usr/bin/env python3
"""Test script pour vérifier que l'API Vercel fonctionne correctement"""

from index import app, handler
from fastapi.testclient import TestClient

def test_app():
    print("Testing FastAPI app via TestClient...")
    client = TestClient(app)
    
    # Test health endpoint
    response = client.get("/api/health")
    print(f"✅ /api/health: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: {data.get('status')}")
        print(f"   Version: {data.get('version')}")
    
    # Test handler
    print("\nTesting via handler...")
    client_handler = TestClient(handler)
    response = client_handler.get("/api/health")
    print(f"✅ handler /api/health: {response.status_code}")
    
    print(f"\nApp routes count: {len(app.routes)}")
    print("Sample routes:")
    for route in app.routes[:10]:
        print(f"  - {route.path}")

if __name__ == "__main__":
    test_app()