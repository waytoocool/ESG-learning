import os
import boto3
from flask import current_app
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3_client = None
        if current_app.config.get('AWS_ACCESS_KEY_ID') and \
           current_app.config.get('AWS_SECRET_ACCESS_KEY') and \
           current_app.config.get('AWS_S3_BUCKET_NAME'):
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
                    aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
                    region_name=current_app.config['AWS_REGION']
                )
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")

    def _get_bucket_name(self):
        return current_app.config.get('AWS_S3_BUCKET_NAME')

    def upload_file(self, file_obj, object_name, content_type=None):
        """
        Upload a file to S3 or local storage fallback.
        :param file_obj: File-like object
        :param object_name: Destination path/name
        :param content_type: MIME type
        :return: Path/URL to file or None
        """
        if self.s3_client:
            try:
                extra_args = {}
                if content_type:
                    extra_args['ContentType'] = content_type
                
                self.s3_client.upload_fileobj(
                    file_obj,
                    self._get_bucket_name(),
                    object_name,
                    ExtraArgs=extra_args
                )
                return object_name
            except ClientError as e:
                logger.error(f"S3 Upload Error: {e}")
                raise e
        else:
            # Fallback to local storage (mostly for dev/test without AWS)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            # Ensure safe path
            full_path = os.path.join(upload_folder, object_name)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Reset file pointer if needed
            file_obj.seek(0)
            with open(full_path, 'wb') as f:
                f.write(file_obj.read())
            
            return full_path

    def delete_file(self, object_name):
        """Delete a file from S3 or local storage."""
        if self.s3_client:
            try:
                self.s3_client.delete_object(
                    Bucket=self._get_bucket_name(),
                    Key=object_name
                )
                return True
            except ClientError as e:
                logger.error(f"S3 Delete Error: {e}")
                return False
        else:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            full_path = os.path.join(upload_folder, object_name)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False

    def download_file(self, object_name):
        """
        Download file from S3 or local storage.
        :return: BytesIO object or file path
        """
        if self.s3_client:
            try:
                # Determine Content-Type/Disposition if possible, but mainly getting the body
                response = self.s3_client.get_object(
                    Bucket=self._get_bucket_name(),
                    Key=object_name
                )
                return response['Body']
            except ClientError as e:
                logger.error(f"S3 Download Error: {e}")
                raise e
        else:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            full_path = os.path.join(upload_folder, object_name)
            if os.path.exists(full_path):
                return open(full_path, 'rb')
            raise FileNotFoundError(f"File {object_name} not found in local storage")

    def generate_presigned_url(self, object_name, expiration=3600):
        """Generate a presigned URL to share an S3 object."""
        if self.s3_client:
            try:
                response = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self._get_bucket_name(),
                        'Key': object_name
                    },
                    ExpiresIn=expiration
                )
                return response
            except ClientError as e:
                logger.error(f"S3 Presigned URL Error: {e}")
                return None
        return None

def get_s3_service():
    """Factory to get initialized S3 Service."""
    return S3Service()
