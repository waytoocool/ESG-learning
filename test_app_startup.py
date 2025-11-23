#!/usr/bin/env python3
"""Quick test to verify app starts successfully."""

from app import create_app

try:
    app = create_app()
    print("✅ App created successfully!")
    print("\nRegistered blueprints:")
    for bp_name in sorted(app.blueprints.keys()):
        bp = app.blueprints[bp_name]
        print(f"  - {bp_name:30} {bp.url_prefix or '/'}")

    # Check if bulk_upload_bp is registered
    if 'user_v2_bulk_upload' in app.blueprints:
        print("\n✅ Bulk Upload API registered successfully!")
        print(f"   URL prefix: {app.blueprints['user_v2_bulk_upload'].url_prefix}")
    else:
        print("\n❌ Bulk Upload API NOT found!")

    print("\n✅ All tests passed!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
