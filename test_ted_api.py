"""
Quick test of Ted's API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_ted_status():
    """Test GET /api/super-admin/ted-status"""
    print("\n🧪 Testing GET /api/super-admin/ted-status...")
    response = requests.get(f"{BASE_URL}/api/super-admin/ted-status")
    data = response.json()
    
    if data.get('success'):
        print("✅ Ted status retrieved successfully!")
        print(f"   Performance Score: {data['ted']['performance_score']}/100")
        print(f"   Job Security: {data['ted']['job_security']}%")
        print(f"   Mood: {data['ted']['mood']}")
        print(f"   Filler Timing: {data['ted']['current_filler_ms']}ms")
        print(f"   Negative Feedback: {data['ted']['negative_feedback_count']} times")
    else:
        print(f"❌ Failed: {data.get('error')}")
    
    return data

def test_ted_negative_feedback():
    """Test POST /api/super-admin/ted-feedback (negative)"""
    print("\n🧪 Testing negative feedback (double-click)...")
    response = requests.post(
        f"{BASE_URL}/api/super-admin/ted-feedback",
        json={"type": "negative"}
    )
    data = response.json()
    
    if data.get('success'):
        print("✅ Ted received negative feedback!")
        print(f"   Performance Score: {data['performance_score']}/100")
        print(f"   Job Security: {data['job_security']}%")
        print(f"   Mood: {data['mood']}")
    else:
        print(f"❌ Failed: {data.get('error')}")
    
    return data

def test_ted_positive_feedback():
    """Test POST /api/super-admin/ted-feedback (positive)"""
    print("\n🧪 Testing positive feedback (click)...")
    response = requests.post(
        f"{BASE_URL}/api/super-admin/ted-feedback",
        json={"type": "positive"}
    )
    data = response.json()
    
    if data.get('success'):
        print("✅ Ted received positive feedback!")
        print(f"   Performance Score: {data['performance_score']}/100")
        print(f"   Job Security: {data['job_security']}%")
        print(f"   Mood: {data['mood']}")
    else:
        print(f"❌ Failed: {data.get('error')}")
    
    return data

if __name__ == "__main__":
    print("=" * 60)
    print("Ted - Virtual Performance Manager API Test")
    print("=" * 60)
    
    # Initial status
    test_ted_status()
    
    # Give Ted some negative feedback
    test_ted_negative_feedback()
    
    # Check status again
    test_ted_status()
    
    # Give Ted positive feedback
    test_ted_positive_feedback()
    
    # Final status
    test_ted_status()
    
    print("\n" + "=" * 60)
    print("✅ All Ted API tests complete!")
    print("=" * 60)
