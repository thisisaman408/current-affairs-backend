"""
IST Timezone Utilities
"""
from datetime import datetime, date, tzinfo
from typing import cast
from src.config import settings
from typing import Union
import pytz

IST = settings.IST
def now_ist() -> datetime:
    """Current datetime in IST"""
    return datetime.now(cast(tzinfo, IST))

def today_ist() -> date:
    """Today's date in IST"""
    return now_ist().date()

def to_ist(dt_or_str: Union[datetime, str]) -> datetime:
    """Convert UTC datetime or ISO string to IST"""
    if isinstance(dt_or_str, str):
        dt = datetime.fromisoformat(dt_or_str.replace('Z', '+00:00'))
    else:
        dt = dt_or_str
    
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    return dt.astimezone(IST)

def parse_date_ist(date_str: str) -> date:
    """
    Parse YYYY-MM-DD to IST date
    """
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def format_ist(dt: datetime) -> str:
    """Format datetime for display"""
    ist_dt = to_ist(dt)
    return ist_dt.strftime("%d %b %Y, %I:%M %p")
