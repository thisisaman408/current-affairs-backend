# test_backend.py
import requests
from datetime import datetime, timedelta

# Paste the JWT token from console logs here
TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImE1YTAwNWU5N2NiMWU0MjczMDBlNTJjZGQ1MGYwYjM2Y2Q4MDYyOWIiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiQW1hbiIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9jdXJyZW50LWFmZmFpcnMtNGQ1ODkiLCJhdWQiOiJjdXJyZW50LWFmZmFpcnMtNGQ1ODkiLCJhdXRoX3RpbWUiOjE3NjA0NjcwNDcsInVzZXJfaWQiOiIxQWpHd2pqWm9TVEN2c0Y3c0JxdFZmOFZXOU0yIiwic3ViIjoiMUFqR3dqalpvU1RDdnNGN3NCcXRWZjhWVzlNMiIsImlhdCI6MTc2MDQ3MzUxMCwiZXhwIjoxNzYwNDc3MTEwLCJlbWFpbCI6InRlc3RAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbInRlc3RAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.fkfljx60_tUwFc6yap8AKSOWaMApz5zqjKpirxwcalc2h06_MRRLmTEXPKmMy0oqBPjRieVSKLJ51Z9vvSW1CHsbo6T8wnV8cYV4s6XYAr3JZowHvWL_qaCNEeARdRr5oSn1uWRYNyNilQfZJ_a3AuhgAbvFa4Yx8-x1Eoh7Iz2bcaK9_3cr7FHPfd_gTL5HTyOSM9B0yYqYz6n70HZhYEXaoLHh5JQJGPDJL1TGJ2JTetu1HA3LYvBhfbr8oGkSqNw1MLUEGZciLTFibuQ_pm-rFJ8WWzNtqLV-LQlCDzYzEHc3nvuxKZlbOSWo_zqja6GQg19h3IpJaUa5nZ09DQ"  

# Your backend URL
BASE_URL = "http://localhost:8000/api/v1"

# Calculate time range (now to tomorrow end)
now = datetime.utcnow()
tomorrow_end = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)

params = {
    "start_time": now.isoformat() + "Z",
    "end_time": tomorrow_end.isoformat() + "Z"
}

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

print(f"🌐 Testing: {BASE_URL}/content/scheduled")
print(f"📅 From: {params['start_time']}")
print(f"📅 To: {params['end_time']}")
print(f"🔑 Token: {TOKEN[:50]}...")

response = requests.get(
    f"{BASE_URL}/content/scheduled",
    params=params,
    headers=headers
)

print(f"\n📊 Status Code: {response.status_code}")
print(f"📦 Response:")
print(response.json())
