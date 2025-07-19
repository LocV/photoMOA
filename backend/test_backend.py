import requests
import json

def test_backend():
    """Test if the backend is running and responding"""
    try:
        # Test health endpoint
        response = requests.get('http://localhost:5001/api/health')
        if response.status_code == 200:
            print("✓ Backend health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"✗ Backend health check failed with status {response.status_code}")
            
        # Test history endpoint
        response = requests.get('http://localhost:5001/api/history')
        if response.status_code == 200:
            print("✓ History endpoint working")
            history = response.json()
            print(f"Found {len(history)} entries in history")
        else:
            print(f"✗ History endpoint failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend. Make sure it's running on localhost:5001")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_backend()
