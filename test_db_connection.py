
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def test_db_connection():
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL is not set.")
        return False
        
    print(f"Testing connection to: {db_url.split('@')[-1]}") 
    
    try:
        engine = create_engine(db_url, connect_args={'connect_timeout': 10})
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"✅ Connection Successful! Result: {result.scalar()}")
            return True
            
    except Exception as e:
        print(f"❌ Connection Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_db_connection()
