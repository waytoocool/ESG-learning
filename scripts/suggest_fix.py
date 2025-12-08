import os
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def suggest_fix():
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    supabase_url = os.environ.get('SUPABASE_URL') or os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL not set")
        return

    print(f"Current DATABASE_URL Host: {urllib.parse.urlparse(db_url).hostname}")

    project_ref = None
    if supabase_url:
        try:
            # Format: https://[project-ref].supabase.co
            parsed = urllib.parse.urlparse(supabase_url)
            hostname = parsed.hostname
            if hostname:
                project_ref = hostname.split('.')[0]
                print(f"ℹ️  Found Project Ref from SUPABASE_URL: {project_ref}")
        except:
            pass
    
    if not project_ref:
        # Try DIRECT_URL if it exists and looks different?
        # Often DIRECT_URL is also a pooler url or session url, but if it is 'db.[project-ref].supabase.co' we can use it.
        direct_url = os.environ.get('DIRECT_URL')
        if direct_url:
             parsed_direct = urllib.parse.urlparse(direct_url)
             if 'supabase.co' in parsed_direct.hostname and 'pooler' not in parsed_direct.hostname:
                 # e.g. db.abcdefg.supabase.co
                 parts = parsed_direct.hostname.split('.')
                 if len(parts) >= 3:
                     project_ref = parts[1] # db.[PROJECT_REF].supabase.co
                     print(f"ℹ️  Found Project Ref from DIRECT_URL: {project_ref}")

    if not project_ref:
        print("❌ Could not automatically determine Project Ref from environment.")
        return

    # Construct new URL
    parsed_db = urllib.parse.urlparse(db_url)
    if 'pooler' in parsed_db.hostname or parsed_db.port == 6543:
        current_user = parsed_db.username
        if '.' not in current_user:
            new_user = f"{current_user}.{project_ref}"
            print(f"💡 Suggested Username: {new_user}")
            
            # Reconstruct URL
            new_url = db_url.replace(f"{current_user}:", f"{new_user}:")
            
            print(f"\nAttempting connection with FIXED username...")
            try:
                engine = create_engine(new_url, connect_args={'connect_timeout': 5})
                with engine.connect() as connection:
                    result = connection.execute(text("SELECT 1"))
                    print(f"✅ FIXED Connection Successful! Result: {result.scalar()}")
                    print("\nRecommended Action:")
                    print(f"Update your DATABASE_URL to use the username: {new_user}")
            except Exception as e:
                print(f"❌ Fixed connection failed: {e}")
        else:
            print("ℹ️  Username already contains a dot. Maybe it's the wrong project ref?")

if __name__ == "__main__":
    suggest_fix()
