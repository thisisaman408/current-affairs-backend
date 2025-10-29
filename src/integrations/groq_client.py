"""
Groq AI Client - JSON Object Mode with Rich Content
Generates detailed Hinglish content with title, description, explanation
"""
from groq import Groq
from src.config import settings
from src.constants import HINGLISH_SYSTEM_PROMPT, EXAM_FOCUS
import json
import logging

logger = logging.getLogger(__name__)


class GroqClient:
    """Groq API client for rich Hinglish content generation"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        logger.info(f"✅ Groq initialized: {self.model}")
    
    def generate_content(
        self,
        text_chunk: str,
        exam_types: list[str],
        date_from: str,
        date_to: str
    ) -> list[dict]:
        """Generate rich Hinglish facts + questions using JSON Object Mode"""
        
        exam_instructions = "\n".join([
            f"- {exam}: {EXAM_FOCUS.get(exam, 'General')}"
            for exam in exam_types
        ])
        
        prompt = f"""{HINGLISH_SYSTEM_PROMPT}

**EXAM TYPES**: {', '.join(exam_types)}
**DATE RANGE**: {date_from} to {date_to}
**FOCUS**: {exam_instructions}

**TEXT**:
{text_chunk[:2500]}

**TASK**:
Generate 6-8 Hinglish items (both facts AND questions in 85:15 ratio).

IMPORTANT: Return ONLY a JSON object with this EXACT structure:

FOR FACTS:
{{
  "items": [
    {{
      "text": "Short version (50-100 chars)",
      "title": "भारत का नया कानून",
      "description": "Arre bhai, India ne naya data protection law pass kiya hai jo sabhi companies ko user ka data safely rakhna padega. GDPR jaisa hai but India ke liye customize kiya gaya hai.",
      "explanation": "Yeh law isliye important hai kyunki cyber attacks aur data breaches badh rahe hain. Government chahti hai ki citizens ka personal data secure rahe.",
      "type": "fact",
      "exam": "UPSC",
      "category": "Polity"
    }}
  ]
}}

FOR QUESTIONS (MCQ):
{{
  "items": [
    {{
      "text": "Short question version (50-100 chars)",
      "title": "डेटा प्रोटेक्शन कानून कब पास हुआ?",
      "description": "Arre bhai, India ka new Data Protection Act kab pass hua tha?",
      "explanation": "Yeh act 2023 mein pass hua tha aur 2024 mein implement ho gaya. Iska main purpose hai citizens ka personal data protect karna aur companies ko accountable banana.",
      "options": ["A) 2021", "B) 2022", "C) 2023", "D) 2024"],
      "correct_answer": "C",
      "type": "question",
      "exam": "UPSC",
      "category": "Polity"
    }}
  ]
}}

**STRICT RULES**:
1. 85% FACTS, 15% QUESTIONS
2. ALL text fields MUST be Hinglish (Hindi+English mix)
3. title MUST be in Hindi (Devanagari script)
4. description MUST be 2-3 sentences, conversational, starts with "Arre bhai" or "Dekh" or "Sunn"
5. explanation MUST explain WHY it matters or HOW it works
6. For questions: options MUST be array of 4 options in format ["A) ...", "B) ...", "C) ...", "D) ..."]
7. For questions: correct_answer MUST be "A", "B", "C", or "D"
8. exam MUST be one of: {', '.join(exam_types)}
9. category MUST be meaningful (Polity, Economy, IR, Geography, etc.)
10. Return ONLY valid JSON, nothing else
"""
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Hinglish current affairs content creator for Indian competitive exams. You ONLY respond with valid JSON objects containing rich, detailed Hinglish content. Never use plain text responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.6,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            logger.info(f"📥 Response: {len(content)} chars, finish: {finish_reason}")
            
            # Parse JSON
            result = json.loads(content)
            items = result.get("items", [])
            
            if items:
                # Validate each item
                valid_items = []
                for item in items:
                    if self._validate_item(item):
                        valid_items.append(item)
                    else:
                        logger.warning(f"⚠️ Invalid item skipped: {item.get('text', 'NO TEXT')[:50]}")
                
                logger.info(f"✅ Generated {len(valid_items)} valid items")
                return valid_items
            else:
                logger.warning("⚠️ No items in response")
                return []
                    
        except Exception as e:
            logger.error(f"❌ Groq API error: {e}")
            return []
    
    def _validate_item(self, item: dict) -> bool:
        """Validate item structure"""
        # Required for ALL items
        if not item.get('text'):
            return False
        if not item.get('title'):
            return False
        if not item.get('description'):
            return False
        if item.get('type') not in ['fact', 'question']:
            return False
        
        # Required for questions
        if item.get('type') == 'question':
            options = item.get('options')
            if not isinstance(options, list):
                return False
            if len(options) != 4:
                return False
            if item.get('correct_answer') not in ['A', 'B', 'C', 'D']:
                return False
        
        return True


# Global instance
groq_client = GroqClient()
