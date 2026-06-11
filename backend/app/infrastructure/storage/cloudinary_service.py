"""
Cloudinary storage service for uploaded books.
"""

import asyncio
import logging

import cloudinary
import cloudinary.uploader

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

# Initialize Cloudinary config singleton (only if URL is set)
_settings = get_settings()
if _settings.CLOUDINARY_URL:
    cloudinary.config(url=_settings.CLOUDINARY_URL)


class CloudinaryUploadError(Exception):
    """Raised when an error occurs during upload."""


class CloudinaryService:
    """Service for handling file uploads to Cloudinary."""

    async def upload_pdf(self, file_bytes: bytes, filename: str) -> str:
        """
        Uploads a PDF to Cloudinary under the 'ai_librarian/books' folder.
        Returns the secure URL. Raises CloudinaryUploadError on failure.
        """
        if not get_settings().CLOUDINARY_URL:
            raise CloudinaryUploadError(
                "CLOUDINARY_URL belum dikonfigurasi. Tidak dapat mengunggah file."
            )

        # Determine public_id (without extension)
        public_id = filename
        if public_id.lower().endswith(".pdf"):
            public_id = public_id[:-4]

        try:
            # Cloudinary upload is blocking, run in a thread
            response = await asyncio.to_thread(
                cloudinary.uploader.upload,
                file_bytes,
                folder="ai_librarian/books",
                public_id=public_id,
                resource_type="raw",  # Use 'raw' to avoid image transformations on PDF
                overwrite=True,
            )
            secure_url = response.get("secure_url")
            logger.info(f"Successfully uploaded {filename} to Cloudinary: {secure_url}")
            return secure_url
        except Exception as e:
            logger.error(f"Failed to upload {filename} to Cloudinary: {e}")
            raise CloudinaryUploadError(f"Cloudinary upload failed: {str(e)}") from e
