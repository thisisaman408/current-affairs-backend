"""
Test Groq API directly to see what's happening
"""
from groq import Groq
from src.config import settings
import json

client = Groq(api_key=settings.GROQ_API_KEY)

test_text = """
India-China Relations
Why in News?
The 24th round of India-China border talks emphasized peaceful resolution.
Both nations discussed trade cooperation and border de-escalation.
"""

print("🧪 Testing Groq API...\n")
print(f"Model: {settings.GROQ_MODEL}")
print(f"API Key: {settings.GROQ_API_KEY[:20]}...\n")

try:
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "Return ONLY valid JSON array."
            },
            {
                "role": "user",
                "content": f"""Generate 3 Hinglish facts from this text:
{test_text}

Format:
[
  {{"text": "Arre bhai, India-China...", "type": "fact", "exam": "UPSC", "category": "IR"}}
]
"""
            }
        ],
        model=settings.GROQ_MODEL,
        temperature=0.5,
        max_tokens=500
    )
    
    content = response.choices[0].message.content
    
    print(f"✅ Response received!")
    print(f"📏 Length: {len(content)} characters")
    print(f"📦 Content:\n{content}\n")
    
    # Try to parse
    try:
        items = json.loads(content)
        print(f"✅ JSON valid! Items: {len(items)}")
    except Exception as e:
        print(f"❌ JSON invalid: {e}")
        
except Exception as e:
    print(f"❌ API Error: {e}")
