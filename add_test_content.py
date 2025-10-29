"""
Add test content to database
Run this once: python add_test_content.py
"""
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.models.question import Question
from datetime import date

def add_test_content():
    db = next(get_db())
    test_data = [
        Question(
            content_type="fact",
            exam_type="UPSC",
            title="भारत की राजधानी",
            description="Delhi India ki capital hai aur yeh country ka administrative center hai. Yahan par sab government offices aur Parliament hai.",
            explanation="Delhi ko 1911 mein capital banaya gaya tha, British rule ke time.",
            date_from=date(2025, 10, 1),
            date_to=date(2025, 10, 31)
        ),
        Question(
            content_type="question",
            exam_type="UPSC",
            title="भारत का पहला प्रधानमंत्री कौन था?",
            description="India ke first Prime Minister kaun the?",
            explanation="Jawaharlal Nehru India ke pehle PM the, unhone 1947 mein office sambhala.",
            options=["A) Mahatma Gandhi", "B) Jawaharlal Nehru", "C) Sardar Patel", "D) Dr. Rajendra Prasad"],
            correct_answer="B",
            date_from=date(2025, 10, 1),
            date_to=date(2025, 10, 31)
        ),
        Question(
            content_type="fact",
            exam_type="SSC",
            title="भारत का सबसे बड़ा राज्य",
            description="Rajasthan India ka sabse bada state hai area ke hisab se.",
            explanation="Rajasthan 342,239 sq km area cover karta hai.",
            date_from=date(2025, 10, 1),
            date_to=date(2025, 10, 31)
        ),
    ]
    
    for item in test_data:
        db.add(item)
    
    db.commit()
    print("✅ Test content added successfully!")
    db.close()

if __name__ == "__main__":
    add_test_content()
