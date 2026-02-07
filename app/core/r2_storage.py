"""
Cloudflare R2 Storage Service
Handles video and thumbnail uploads/downloads
"""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import os
import uuid
from datetime import datetime
from typing import Optional, Tuple
import mimetypes

# R2 Configuration
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "a9d357f79343d4038c9957eb52fdca6e")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "f2c1fd313dd4d51f0f101a679cff48f9")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "14f3b43a343dc54c6c0ffdb180c8982669453b6766c2a1f92387e53e521bd270")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "flight-academy-videos")
R2_ENDPOINT = os.getenv("R2_ENDPOINT", f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com")

# Public URL for accessing files (set after enabling public access)
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "https://pub-915af40a190e4aaeae419a28034c0a3a.r2.dev")

# Initialize S3 client for R2
def get_r2_client():
    """Get boto3 S3 client configured for Cloudflare R2"""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(
            signature_version='s3v4',
            retries={'max_attempts': 3}
        ),
        region_name='auto'
    )


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """Generate a unique filename with timestamp and UUID"""
    ext = os.path.splitext(original_filename)[1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    if prefix:
        return f"{prefix}/{timestamp}_{unique_id}{ext}"
    return f"{timestamp}_{unique_id}{ext}"


async def upload_file(
    file_content: bytes,
    original_filename: str,
    folder: str = "videos",
    content_type: Optional[str] = None
) -> Tuple[bool, str, str]:
    """
    Upload a file to R2
    
    Args:
        file_content: File bytes
        original_filename: Original filename
        folder: Folder prefix (videos, thumbnails, etc.)
        content_type: MIME type
    
    Returns:
        Tuple of (success, r2_key, public_url)
    """
    try:
        client = get_r2_client()
        
        # Generate unique key
        key = generate_unique_filename(original_filename, folder)
        
        # Detect content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(original_filename)
            content_type = content_type or 'application/octet-stream'
        
        # Upload to R2
        client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=key,
            Body=file_content,
            ContentType=content_type,
        )
        
        # Generate public URL
        if R2_PUBLIC_URL:
            public_url = f"{R2_PUBLIC_URL}/{key}"
        else:
            # Generate presigned URL if no public access
            public_url = client.generate_presigned_url(
                'get_object',
                Params={'Bucket': R2_BUCKET_NAME, 'Key': key},
                ExpiresIn=3600 * 24 * 7  # 7 days
            )
        
        return True, key, public_url
        
    except ClientError as e:
        print(f"R2 Upload Error: {e}")
        return False, "", str(e)
    except Exception as e:
        print(f"Upload Error: {e}")
        return False, "", str(e)


async def delete_file(key: str) -> bool:
    """Delete a file from R2"""
    try:
        client = get_r2_client()
        client.delete_object(Bucket=R2_BUCKET_NAME, Key=key)
        return True
    except Exception as e:
        print(f"Delete Error: {e}")
        return False


async def get_presigned_url(key: str, expires_in: int = 3600) -> Optional[str]:
    """Get a presigned URL for a file"""
    try:
        client = get_r2_client()
        url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': R2_BUCKET_NAME, 'Key': key},
            ExpiresIn=expires_in
        )
        return url
    except Exception as e:
        print(f"Presigned URL Error: {e}")
        return None


async def get_presigned_upload_url(
    filename: str,
    folder: str = "videos",
    expires_in: int = 3600
) -> Tuple[Optional[str], str]:
    """
    Get a presigned URL for direct upload from client
    
    Returns:
        Tuple of (presigned_url, key)
    """
    try:
        client = get_r2_client()
        key = generate_unique_filename(filename, folder)
        
        url = client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': R2_BUCKET_NAME,
                'Key': key,
            },
            ExpiresIn=expires_in
        )
        return url, key
    except Exception as e:
        print(f"Presigned Upload URL Error: {e}")
        return None, ""


def list_files(prefix: str = "", max_keys: int = 100) -> list:
    """List files in the bucket"""
    try:
        client = get_r2_client()
        response = client.list_objects_v2(
            Bucket=R2_BUCKET_NAME,
            Prefix=prefix,
            MaxKeys=max_keys
        )
        
        files = []
        for obj in response.get('Contents', []):
            files.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat(),
            })
        return files
    except Exception as e:
        print(f"List Error: {e}")
        return []
