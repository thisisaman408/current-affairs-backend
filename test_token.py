# test_token.py
from jose import jwt
from datetime import datetime, timedelta
import os

# Load from .env or use default
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-here")

# Test user details
user_id = 4
email = "test@example.com"

# Create JWT payload
payload = {
    "sub": email,
    "user_id": user_id,
    "exp": datetime.utcnow() + timedelta(days=30)
}

# Generate token
token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

print("=" * 80)
print("🔑 JWT TOKEN FOR USER ID:", user_id)
print("=" * 80)
print(token)
print("=" * 80)
print("\n📋 CURL COMMAND:")
print("=" * 80)
print(f'''curl -X GET "http://localhost:8000/api/v1/content/daily-sync" \\
  -H "Authorization: Bearer {token}" \\
  | jq .''')
print("=" * 80)
