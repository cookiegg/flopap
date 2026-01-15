import httpx
import json
from datetime import date

# Configuration
BASE_URL = "http://localhost:8000/api/v1/internal"
TOKEN = "test-token-123"

def test_export():
    print("\n--- Testing Export (Cloud -> Local) ---")
    headers = {"X-Internal-Token": TOKEN}
    url = f"{BASE_URL}/export/users"
    
    response = httpx.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Profiles found: {data['count_profiles']}")
        print(f"Feedback found: {data['count_feedback']}")
        if data['profiles']:
             print(f"Sample Profile User: {data['profiles'][0]['user_id']}")
    else:
        print(f"Error: {response.text}")

def test_ingest_rankings():
    print("\n--- Testing Ingest Rankings (Local -> Cloud) ---")
    headers = {"X-Internal-Token": TOKEN, "Content-Type": "application/json"}
    url = f"{BASE_URL}/ingest/batch"
    
    # We need a valid arxiv_id from the DB
    paper_id = "2512.23903v1"
    
    payload = {
        "rankings": [
            {
                "user_id": "test_user_01",
                "pool_date": str(date.today()),
                "source_key": "arxiv_day_" + date.today().strftime("%Y%m%d"),
                "paper_ids": [paper_id],
                "scores": [0.95]
            }
        ]
    }
    
    response = httpx.post(url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    test_export()
    test_ingest_rankings()
