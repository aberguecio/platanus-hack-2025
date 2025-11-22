import os
import boto3
from typing import Optional
from datetime import datetime
import uuid

class S3Service:
    """Service for S3 file storage (placeholder/mock for now)"""

    def __init__(self, bucket_name: Optional[str] = None):
        self.bucket_name = bucket_name or os.getenv("AWS_S3_BUCKET")
        self.enabled = bool(self.bucket_name)

        if self.enabled:
            # Use credentials from environment
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "us-east-1")
            )
            print(f"[S3] Initialized with bucket: {self.bucket_name}")
        else:
            self.s3_client = None
            print("[S3] Running in mock mode (no bucket configured)")

    async def upload_image(
        self,
        image_data: bytes,
        filename: Optional[str] = None
    ) -> str:
        """
        Upload image to S3 and return the S3 key (path).
        If S3 is not configured, returns a placeholder URL.
        """
        if not self.enabled:
            # Mock/placeholder implementation
            mock_filename = filename or f"{uuid.uuid4()}.jpg"
            return f"http://placeholder.local/images/{mock_filename}"

        # Real S3 implementation
        if not filename:
            filename = f"{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4()}.jpg"

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=filename,
            Body=image_data,
            ContentType='image/jpeg'
        )

        # Return the S3 key (we'll generate presigned URLs when retrieving)
        return f"s3://{self.bucket_name}/{filename}"

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for an S3 object.

        Args:
            s3_key: S3 key in format "s3://bucket/path" or just "path"
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned URL string
        """
        if not self.enabled:
            print(f"[S3] generate_presigned_url called but S3 is disabled (mock mode)")
            return s3_key  # Return as-is for mock mode

        print(f"[S3] Generating presigned URL for: {s3_key}")

        # Extract bucket and key from s3:// URI if needed
        if s3_key.startswith("s3://"):
            parts = s3_key.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""
        else:
            bucket = self.bucket_name
            key = s3_key

        print(f"[S3] Bucket: {bucket}, Key: {key}")

        # Generate presigned URL
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            print(f"[S3] Presigned URL generated successfully: {url[:100]}...")
            return url
        except Exception as e:
            print(f"[S3] Error generating presigned URL: {e}")
            import traceback
            traceback.print_exc()
            return s3_key  # Fallback to original
