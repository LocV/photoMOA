#!/usr/bin/env python3

import requests
import json

# Test the update-shots endpoint
url = "http://localhost:5001/api/update-shots/test_id"
data = {
    "manual_shots": [[100, 200, 10], [300, 400, 10]]
}

try:
    response = requests.post(url, 
                           headers={'Content-Type': 'application/json'},
                           json=data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")
