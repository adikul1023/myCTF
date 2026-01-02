"""
Storage Client - S3-compatible storage (MinIO) client for artifact management.
"""

import hashlib
import io
from typing import Optional, BinaryIO
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from ..core.config import settings


class StorageClient:
    """
    S3-compatible storage client for managing forensic artifacts.
    
    Uses MinIO for local development and can be configured
    for any S3-compatible storage in production.
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        secure: Optional[bool] = None,
        public_endpoint: Optional[str] = None,
    ):
        """
        Initialize the storage client.
        
        Supports MinIO (local), Cloudflare R2, AWS S3, and any S3-compatible storage.
        
        Args:
            endpoint: S3-compatible endpoint (e.g., account-id.r2.cloudflarestorage.com for R2).
            access_key: Access key ID.
            secret_key: Secret access key.
            bucket_name: Default bucket name.
            secure: Use HTTPS (True for production/R2).
            public_endpoint: Public endpoint for presigned URLs (e.g., R2.dev subdomain).
        """
        self.endpoint = endpoint or settings.MINIO_ENDPOINT
        self.public_endpoint = public_endpoint or getattr(settings, 'MINIO_PUBLIC_ENDPOINT', None) or self.endpoint
        self.access_key = access_key or settings.MINIO_ACCESS_KEY
        self.secret_key = secret_key or settings.MINIO_SECRET_KEY
        self.bucket_name = bucket_name or settings.MINIO_BUCKET_NAME
        self.secure = secure if secure is not None else settings.MINIO_USE_SSL
        
        # Cloudflare R2 specific: Remove https:// if present in endpoint
        if self.endpoint.startswith('https://'):
            self.endpoint = self.endpoint.replace('https://', '')
        if self.endpoint.startswith('http://'):
            self.endpoint = self.endpoint.replace('http://', '')
        
        self._client: Optional[Minio] = None
        self._public_client: Optional[Minio] = None
    
    @property
    def client(self) -> Minio:
        """Get or create the MinIO client for internal operations."""
        if self._client is None:
            self._client = Minio(
                endpoint=self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
        return self._client
    
    @property
    def public_client(self) -> Minio:
        """Get or create the MinIO client for presigned URLs (public access)."""
        if self._public_client is None:
            self._public_client = Minio(
                endpoint=self.public_endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
        return self._public_client
    
    async def ensure_bucket_exists(self) -> None:
        """
        Ensure the default bucket exists, create if not.
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise StorageError(f"Failed to ensure bucket exists: {e}")
    
    async def upload_file(
        self,
        file_data: BinaryIO,
        object_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload a file to storage.
        
        Args:
            file_data: File-like object to upload.
            object_name: Name/path for the object in storage.
            content_type: MIME type of the file.
            metadata: Additional metadata to store with the object.
        
        Returns:
            The storage path of the uploaded file.
        """
        try:
            # Get file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Seek back to start
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type or "application/octet-stream",
                metadata=metadata,
            )
            
            return f"{self.bucket_name}/{object_name}"
        
        except S3Error as e:
            raise StorageError(f"Failed to upload file: {e}")
    
    async def download_file(
        self,
        object_name: str,
    ) -> bytes:
        """
        Download a file from storage.
        
        Args:
            object_name: Name/path of the object in storage.
        
        Returns:
            File contents as bytes.
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
            )
            return response.read()
        except S3Error as e:
            raise StorageError(f"Failed to download file: {e}")
        finally:
            response.close()
            response.release_conn()
    
    async def get_presigned_download_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1),
    ) -> str:
        """
        Generate a presigned URL for downloading a file.
        
        Args:
            object_name: Name/path of the object in storage.
            expires: URL expiration time.
        
        Returns:
            Presigned download URL (with public endpoint for browser access).
        """
        try:
            # Generate URL using internal client (which can reach MinIO)
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires,
            )
            # Replace internal endpoint with public endpoint for browser access
            if self.endpoint != self.public_endpoint:
                url = url.replace(self.endpoint, self.public_endpoint, 1)
            return url
        except S3Error as e:
            raise StorageError(f"Failed to generate presigned URL: {e}")
    
    async def get_presigned_upload_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1),
    ) -> str:
        """
        Generate a presigned URL for uploading a file.
        
        Args:
            object_name: Name/path for the object in storage.
            expires: URL expiration time.
        
        Returns:
            Presigned upload URL.
        """
        try:
            return self.client.presigned_put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires,
            )
        except S3Error as e:
            raise StorageError(f"Failed to generate presigned upload URL: {e}")
    
    async def delete_file(self, object_name: str) -> None:
        """
        Delete a file from storage.
        
        Args:
            object_name: Name/path of the object to delete.
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
            )
        except S3Error as e:
            raise StorageError(f"Failed to delete file: {e}")
    
    async def file_exists(self, object_name: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            object_name: Name/path of the object.
        
        Returns:
            True if the file exists, False otherwise.
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
            )
            return True
        except S3Error:
            return False
    
    @staticmethod
    def calculate_sha256(file_data: BinaryIO) -> str:
        """
        Calculate SHA-256 hash of a file.
        
        Args:
            file_data: File-like object.
        
        Returns:
            Hex-encoded SHA-256 hash.
        """
        sha256_hash = hashlib.sha256()
        file_data.seek(0)
        
        for chunk in iter(lambda: file_data.read(8192), b""):
            sha256_hash.update(chunk)
        
        file_data.seek(0)
        return sha256_hash.hexdigest()


class StorageError(Exception):
    """Exception raised for storage operations."""
    pass


# Global storage client instance
storage_client = StorageClient()
