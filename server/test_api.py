#!/usr/bin/env python3
"""
Simple test script to verify the Llama API integration
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_analyze_endpoint():
    """Test the analyze endpoint"""
    print("\nTesting analyze endpoint...")
    
    test_data = {
        "text": "This is a sample text that I want to analyze to determine if it was written by AI or a human. The text contains natural language patterns and should be processed by the Llama API."
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            headers={"Content-Type": "application/json"},
            json=test_data
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Starting API tests...")
    print("Make sure the server is running with: uvicorn main:app --reload")
    print("=" * 50)
    
    health_ok = test_health_endpoint()
    analyze_ok = test_analyze_endpoint()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Health endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Analyze endpoint: {'✅ PASS' if analyze_ok else '❌ FAIL'}")
    
    if health_ok and analyze_ok:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the server logs.")
