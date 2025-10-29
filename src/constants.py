"""
Application Constants
Exam types, content types, Hinglish instructions
"""
from enum import Enum
from typing import Dict

class ExamType(str, Enum):
    """Supported exam types"""
    General = "General"
    UPSC = "UPSC"
    SSC = "SSC"
    BANKING = "Banking"
    RAILWAY = "Railway"
    DEFENCE = "Defence"

class ContentType(str, Enum):
    """Content types for generation"""
    FACT = "fact"        # 85% - Direct information
    QUESTION = "question" # 15% - Quiz style

class JobStatus(str, Enum):
    """PDF processing job statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class LanguageStyle(str, Enum):
    """Output language styles"""
    HINGLISH = "hinglish"  # Default: 60% Hindi + 40% English
    HINDI = "hindi"        # Pure Hindi (future)

# Hinglish Generation Instructions
HINGLISH_SYSTEM_PROMPT = """
Tu ek expert current affairs content creator hai jo HINGLISH mein facts aur questions banata hai.

STYLE RULES:
- 60% Hindi words + 40% English words
- Casual, friendly tone: "Arre bhai", "Dekh yaar", "Sunn na"
- Jaise dost ko whatsapp pe bata rahe ho
- Roman script mein likho (not Devanagari)

CONTENT RATIO:
- 85% FACTS (direct info, no question mark)
- 15% QUESTIONS (quiz style, interesting sawal)

FACTS Examples:
✅ "Arre bhai, Supreme Court ne aaj Delhi mein pollution ki wajah se construction ban kar diya hai!"
✅ "Dekh yaar, Finance Minister ne budget speech mein education ke liye 1.2 lakh crore allocate kiye!"
✅ "PM Modi ji ne G20 summit mein India ki renewable energy targets announce kiye - 500 GW by 2030!"

QUESTIONS Examples:
✅ "Bhai bata, RBI ne repo rate kitna change kiya tha last policy meet mein?"
✅ "Sunn yaar, kis state ne recently plastic ban fully implement kar diya?"
✅ "Dekh, Olympics mein India ko wrestling mein kis player ne medal dilaya tha?"

RULES:
1. Har sentence 150 characters se kam (mobile notification ke liye)
2. Dates, numbers, names clearly mention karo
3. No English jargon - simple words use karo
4. Context khud mein complete hona chahiye
5. Exam-specific focus maintain karo
"""

# Exam-specific focus instructions
EXAM_FOCUS: Dict[str, str] = {
    "General" : "general purpose current affairs",
    "UPSC": "Analytical approach, policy implications, governance issues, cause-effect samjhao",
    "SSC": "Direct facts, dates/names/numbers focus, straightforward recall questions",
    "Banking": "Economy aur RBI policies focus, banking terms simply explain karo",
    "Railway": "Infrastructure developments, transport policies, government schemes",
    "Defence": "Military operations, defence deals, strategic partnerships, geopolitics"
}

# Date formats (IST)
IST_DATE_FORMAT = "%Y-%m-%d"
IST_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
IST_DISPLAY_FORMAT = "%d %b %Y, %I:%M %p"

# Content generation ratios
FACT_PERCENTAGE = 85
QUESTION_PERCENTAGE = 15

# PDF Processing
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
