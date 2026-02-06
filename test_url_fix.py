#!/usr/bin/env python
"""
Test script to verify URL trailing slash fix.
Tests that PUT/PATCH/DELETE requests work without 500 errors.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from users.models import User

def test_http_methods():
    """Test various HTTP methods on endpoints without trailing slashes."""
    client = Client()
    
    # Get a test user
    user = User.objects.first()
    if not user:
        print("❌ No users found in database")
        return
    
    print(f"Testing with user ID: {user.id}\n")
    
    # Test the original failing endpoint
    print("=" * 60)
    print("Testing Original Issue: PUT /api/v1/users/{id}/pi")
    print("=" * 60)
    response = client.put(f'/api/v1/users/{user.id}/pi', content_type='application/json')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 500:
        print("❌ FAILED: Still getting 500 error!")
        print(f"Response: {response.content.decode()[:200]}")
    elif response.status_code in [401, 403]:
        print("✅ SUCCESS: No more 500 error (got auth error as expected)")
    else:
        print(f"⚠️  Got unexpected status: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("Testing Other Endpoints")
    print("=" * 60)
    
    # Test various endpoints
    test_cases = [
        ("GET", f"/api/v1/users/{user.id}"),
        ("PUT", f"/api/v1/users/{user.id}"),
        ("PATCH", f"/api/v1/users/{user.id}"),
        ("DELETE", f"/api/v1/users/{user.id}"),
        ("GET", "/api/v1/users/me"),
        ("GET", "/api/v1/caretakers"),
        ("GET", "/api/v1/projects"),
    ]
    
    for method, url in test_cases:
        if method == "GET":
            response = client.get(url)
        elif method == "PUT":
            response = client.put(url, content_type='application/json')
        elif method == "PATCH":
            response = client.patch(url, content_type='application/json')
        elif method == "DELETE":
            response = client.delete(url)
        
        status_icon = "✅" if response.status_code != 500 else "❌"
        print(f"{status_icon} {method:6} {url:40} -> {response.status_code}")
        
        if response.status_code == 500:
            print(f"   Error: {response.content.decode()[:100]}")

if __name__ == "__main__":
    test_http_methods()
