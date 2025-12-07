
import os
import io
import time
from app import create_app
from app.services.s3_service import get_s3_service

def test_s3_connection():
    print("\n" + "="*70)
    print("S3 CONNECTIVITY & UPLOAD TEST")
    print("="*70)

    app = create_app()
    
    with app.app_context():
        # Print config (masked) to verify loaded
        print(f"AWS_REGION: {app.config.get('AWS_REGION')}")
        bucket = app.config.get('AWS_S3_BUCKET_NAME')
        print(f"AWS_S3_BUCKET_NAME: {bucket}")
        has_key = bool(app.config.get('AWS_ACCESS_KEY_ID'))
        has_secret = bool(app.config.get('AWS_SECRET_ACCESS_KEY'))
        print(f"Has Access Key: {has_key}")
        print(f"Has Secret Key: {has_secret}")
        
        if not (has_key and has_secret and bucket):
            print("\n❌ MISSING CREDENTIALS. Verify .env file.")
            print("Remember: .env variables must be loaded into environment.")
            return False

        s3_service = get_s3_service()
        
        # Test Data
        test_content = b"This is a test file for S3 verification."
        test_filename = f"test_verification_{int(time.time())}.txt"
        test_key = f"verification_tests/{test_filename}"
        
        try:
            # 1. Upload
            print(f"\n1. Attempting URL/Path generation and Upload to: {test_key}")
            file_obj = io.BytesIO(test_content)
            s3_service.upload_file(file_obj, test_key, content_type="text/plain")
            print("   ✅ Upload method completed without error.")
            
            # 2. Download/Read
            print("\n2. Attempting to Read back file...")
            try:
                retrieved_body = s3_service.download_file(test_key)
                content = retrieved_body.read()
                print(f"   Retrieved {len(content)} bytes.")
                if content == test_content:
                    print("   ✅ Content match successful.")
                else:
                    print("   ❌ Content mismatch!")
                    print(f"      Expected: {test_content}")
                    print(f"      Got: {content}")
            except Exception as e:
                print(f"   ❌ Read failed: {e}")
                
            # 3. Clean up
            print("\n3. Cleaning up (Deleting)...")
            s3_service.delete_file(test_key)
            print("   ✅ Delete method completed.")
            
            print("\n🎉 S3 VERIFICATION SUCCESSFUL!")
            return True
            
        except Exception as e:
            print(f"\n❌ S3 OPERATION FAILED: {str(e)}")
            # Check for common issues
            if "InvalidAccessKeyId" in str(e):
                print("   -> Check AWS_ACCESS_KEY_ID")
            elif "SignatureDoesNotMatch" in str(e):
                print("   -> Check AWS_SECRET_ACCESS_KEY")
            elif "NoSuchBucket" in str(e):
                print("   -> Check AWS_S3_BUCKET_NAME")
            elif "AccessDenied" in str(e):
                print("   -> Check IAM Permissions")
            return False

if __name__ == "__main__":
    test_s3_connection()
