"""
AWS S3 service for storing and serving resume PDFs.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class S3Service:
    """Service for uploading and managing PDF files in AWS S3."""
    
    def __init__(
        self, 
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1"
    ):
        """
        Initialize S3 service.
        
        Args:
            bucket_name: S3 bucket name
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region_name: AWS region name
        """
        self.bucket_name = bucket_name
        self.region_name = region_name
        
        # Initialize S3 client
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=region_name
                )
            else:
                # Use default credentials (IAM role, env vars, etc.)
                self.s3_client = boto3.client('s3', region_name=region_name)
                
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise S3ServiceError("AWS credentials not configured")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise S3ServiceError(f"S3 initialization failed: {str(e)}")
    
    async def upload_resume_pdf(
        self, 
        pdf_bytes: bytes,
        resume_id: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Upload PDF resume to S3 and return presigned URL.
        
        Args:
            pdf_bytes: PDF file bytes
            resume_id: Optional resume ID (UUID will be generated if not provided)
            
        Returns:
            Tuple of (presigned_url, resume_id)
        """
        try:
            # Generate resume ID if not provided
            if not resume_id:
                resume_id = str(uuid.uuid4())
            
            # Create S3 key with timestamp and UUID
            timestamp = datetime.utcnow().strftime('%Y%m%d')
            key = f"resumes/{timestamp}/{resume_id}.pdf"
            
            # Upload PDF to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=pdf_bytes,
                ContentType='application/pdf',
                ContentDisposition='inline',
                Metadata={
                    'resume_id': resume_id,
                    'generated_at': datetime.utcnow().isoformat(),
                    'file_size': str(len(pdf_bytes))
                }
            )
            
            # Generate presigned URL (24 hour expiry)
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=86400  # 24 hours
            )
            
            logger.info(f"Successfully uploaded resume {resume_id} to S3")
            return presigned_url, resume_id
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"S3 upload failed: {error_code} - {error_message}")
            raise S3ServiceError(f"Failed to upload to S3: {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {str(e)}")
            raise S3ServiceError(f"Upload failed: {str(e)}")
    
    def validate_bucket_access(self) -> bool:
        """
        Validate that the S3 bucket exists and is accessible.
        
        Returns:
            True if bucket is accessible
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket {self.bucket_name} does not exist")
            elif error_code == '403':
                logger.error(f"Access denied to S3 bucket {self.bucket_name}")
            else:
                logger.error(f"S3 bucket validation failed: {error_code}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error validating S3 bucket: {str(e)}")
            return False
    
    def get_bucket_info(self) -> dict:
        """
        Get information about the S3 bucket.
        
        Returns:
            Dictionary with bucket information
        """
        try:
            # Get bucket location
            location = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
            
            # Get bucket policy (if accessible)
            try:
                policy = self.s3_client.get_bucket_policy(Bucket=self.bucket_name)
                has_policy = True
            except ClientError:
                has_policy = False
            
            return {
                'name': self.bucket_name,
                'region': location.get('LocationConstraint', 'us-east-1'),
                'accessible': True,
                'has_policy': has_policy
            }
            
        except Exception as e:
            logger.error(f"Failed to get bucket info: {str(e)}")
            return {
                'name': self.bucket_name,
                'accessible': False,
                'error': str(e)
            }
    
    def cleanup_old_resumes(self, days_old: int = 30) -> int:
        """
        Clean up old resume files from S3.
        
        Args:
            days_old: Delete files older than this many days
            
        Returns:
            Number of files deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            deleted_count = 0
            
            # List objects in the resumes folder
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix='resumes/')
            
            objects_to_delete = []
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                            objects_to_delete.append({'Key': obj['Key']})
            
            # Delete objects in batches
            if objects_to_delete:
                for i in range(0, len(objects_to_delete), 1000):  # S3 max 1000 per batch
                    batch = objects_to_delete[i:i+1000]
                    
                    response = self.s3_client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={'Objects': batch}
                    )
                    
                    deleted_count += len(response.get('Deleted', []))
            
            logger.info(f"Cleaned up {deleted_count} old resume files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old resumes: {str(e)}")
            return 0


class S3ServiceError(Exception):
    """Custom exception for S3 service errors."""
    pass