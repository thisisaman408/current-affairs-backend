# fix_promo_enum.py
from sqlalchemy import create_engine, text
from src.config import settings  

db_url = settings.DATABASE_URL
if db_url is None:
    raise RuntimeError("DATABASE_URL is not configured")

engine = create_engine(db_url)

with engine.connect() as conn:
    # Step 1: Change column type to VARCHAR temporarily
    conn.execute(text("ALTER TABLE promo_codes ALTER COLUMN promo_type TYPE VARCHAR(20)"))
    conn.commit()
    
    # Step 2: Drop old enum
    conn.execute(text("DROP TYPE IF EXISTS promotype CASCADE"))
    conn.commit()
    
    # Step 3: Create new enum with lowercase
    conn.execute(text("CREATE TYPE promotype AS ENUM ('discount', 'trial')"))
    conn.commit()
    
    # Step 4: Convert column back to enum
    conn.execute(text("ALTER TABLE promo_codes ALTER COLUMN promo_type TYPE promotype USING LOWER(promo_type)::promotype"))
    conn.commit()
    
    print("✅ Fixed promo_type enum!")
    
    # Verify
    result = conn.execute(text("SELECT code, promo_type FROM promo_codes"))
    for row in result:
        print(f"  - {row[0]}: {row[1]}")
