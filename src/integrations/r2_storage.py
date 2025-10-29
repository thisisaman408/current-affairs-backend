"""
Cloudflare R2 Storage Client
S3-compatible storage for PDFs
"""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from src.config import settings
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class R2Storage:
    """Cloudflare R2 storage handler"""
    
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
            region_name=settings.R2_REGION
        )
        self.bucket = settings.R2_BUCKET_NAME
        logger.info(f"✅ R2 Storage initialized: {self.bucket}")
    
    def upload_pdf(self, file_content: bytes, job_id: int, filename: str) -> str:
        """
        Upload PDF to R2
        Returns: R2 key (path)
        """
        # Generate unique key with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = f"pdfs/{job_id}_{timestamp}_{filename}"
        
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_content,
                ContentType='application/pdf'
            )
            logger.info(f"✅ PDF uploaded to R2: {key}")
            return key
        except ClientError as e:
            logger.error(f"❌ R2 upload failed: {e}")
            raise Exception(f"Failed to upload PDF: {str(e)}")
    
    def download_pdf(self, r2_key: str, local_path: str):
        """
        Download PDF from R2 to local path
        For worker processing
        """
        try:
            self.client.download_file(
                Bucket=self.bucket,
                Key=r2_key,
                Filename=local_path
            )
            logger.info(f"✅ PDF downloaded from R2: {r2_key}")
        except ClientError as e:
            logger.error(f"❌ R2 download failed: {e}")
            raise Exception(f"Failed to download PDF: {str(e)}")
    
    def get_pdf_url(self, r2_key: str, expires_in: int = 3600) -> str:
        """
        Generate presigned URL for PDF (temporary access)
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': r2_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"❌ Failed to generate presigned URL: {e}")
            raise Exception(f"Failed to generate URL: {str(e)}")
    
    def delete_pdf(self, r2_key: str):
        """Delete PDF from R2 (if needed)"""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=r2_key)
            logger.info(f"✅ PDF deleted from R2: {r2_key}")
        except ClientError as e:
            logger.error(f"❌ R2 delete failed: {e}")
            raise Exception(f"Failed to delete PDF: {str(e)}")

# Global R2 client
r2_storage = R2Storage()
