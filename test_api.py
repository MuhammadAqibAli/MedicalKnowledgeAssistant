import requests
import json

BASE_URL = "http://localhost:5000"

def print_response(response):
    """Print the API response in a readable format"""
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print(response.text)

# Test root endpoint
print("\n=== Testing Root Endpoint ===")
response = requests.get(f"{BASE_URL}/")
print_response(response)

# Test document types endpoint
print("\n=== Testing Document Types Endpoint ===")
response = requests.get(f"{BASE_URL}/api/v1/document-types")
print_response(response)

# Test models endpoint
print("\n=== Testing Models Endpoint ===")
response = requests.get(f"{BASE_URL}/api/v1/models")
print_response(response)

# Test list documents endpoint
print("\n=== Testing List Documents Endpoint ===")
response = requests.get(f"{BASE_URL}/api/v1/documents")
print_response(response)

# Test search documents endpoint
print("\n=== Testing Search Documents Endpoint ===")
search_data = {
    "query": "diabetes management",
    "doc_type": "Best Practice"
}
response = requests.post(f"{BASE_URL}/api/v1/search", json=search_data)
print_response(response)

print("\nAPI testing completed.")