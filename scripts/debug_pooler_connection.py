import os
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def debug_connection():
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL is not set.")
        return

    print(f"Checking DATABASE_URL...")
    
    try:
        parsed = urllib.parse.urlparse(db_url)
        hostname = parsed.hostname
        port = parsed.port
        username = parsed.username
        
        print(f"Host: {hostname}")
        print(f"Port: {port}")
        print(f"User: {username}")
        
        is_pooler = port == 6543 or (hostname and 'pooler' in hostname)
        
        if is_pooler:
            print("ℹ️  Detected Supabase Transaction Pooler configuration.")
            if username and '.' not in username:
                print("⚠️  WARNING: Username does not appear to contain a project reference (e.g. 'user.projectref').")
                print("   For Supabase Pooler (port 6543), the username must be formatted as: [user].[project_ref]")
            else:
                print("✅ Username format looks correct for pooler (contains dot).")
        else:
            print("ℹ️  Standard Direct Connection (Session Mode) detected.")

        print("\nAttempting connection...")
        engine = create_engine(db_url, connect_args={'connect_timeout': 5})
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"✅ Connection Successful! Result: {result.scalar()}")
            
    except Exception as e:
        print(f"\n❌ Connection Failed: {str(e)}")
        print("\nTroubleshooting Tips:")
        if "Tenant or user not found" in str(e):
             print("- This error confirms the Supabase Pooler could not identify your project.")
             print("- Ensure your DATABASE_URL username is in the format: 'postgres.your-project-ref'")
             print("- Check your Vercel Environment Variables.")

if __name__ == "__main__":
    debug_connection()
