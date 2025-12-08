from app import create_app
import sys

try:
    app = create_app()
    print("Map of rules:")
    for rule in app.url_map.iter_rules():
        print(f"{rule}: {rule.endpoint}")
        
    print("\nCheck for root route:")
    adapter = app.url_map.bind('localhost')
    try:
        match = adapter.match('/', method='GET')
        print(f"Server matches / to: {match}")
    except Exception as e:
        print(f"Error matching /: {e}")

except Exception as e:
    print(f"Failed to create app: {e}")
    sys.exit(1)
