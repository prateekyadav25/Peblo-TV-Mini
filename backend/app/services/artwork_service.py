import os
import json
import uuid
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from typing import Tuple, List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.storage.base import StorageBackend
from app.models.artwork import Artwork

class ArtworkValidationError(Exception):
    pass

class ArtworkService:
    def __init__(self, storage: StorageBackend, reference_data_path: str):
        self.storage = storage
        with open(reference_data_path, 'r', encoding='utf-8') as f:
            self.ref = json.load(f)

    def _validate_image(self, file_content: bytes, artwork_type: str) -> None:
        if artwork_type not in self.ref.get('artwork_specs', {}):
            raise ArtworkValidationError(f"Unknown artwork type '{artwork_type}'.")

        spec = self.ref['artwork_specs'][artwork_type]
        max_bytes = spec['max_kb'] * 1024

        if len(file_content) > max_bytes:
            raise ArtworkValidationError(
                f"File is {len(file_content) // 1024} KB. Maximum allowed is {spec['max_kb']} KB."
            )

        try:
            img = Image.open(BytesIO(file_content))
            img.verify() # verify format
        except UnidentifiedImageError:
            raise ArtworkValidationError("Unsupported or corrupt image format. Please upload a valid JPEG, PNG, or WebP.")

        # Re-open because verify() closes the file pointer
        img = Image.open(BytesIO(file_content))
        width, height = img.size

        # Check aspect ratio
        aspect_str = spec['aspect']
        expected_w, expected_h = map(int, aspect_str.split(':'))
        expected_ratio = expected_w / expected_h
        actual_ratio = width / height
        
        # Exact aspect ratio is rarely perfect, allow a tiny margin of error (1%)
        if abs(actual_ratio - expected_ratio) > 0.01:
            raise ArtworkValidationError(
                f"{artwork_type.capitalize()} image must be {aspect_str}. Your image is {width}×{height} ({actual_ratio:.2f}:1). "
                f"Please upload an image close to {spec['target_px'][0]}×{spec['target_px'][1]}."
            )

        # Require the documented target dimensions while allowing a one-pixel
        # tolerance for image processing tools that round dimensions.
        target_w, target_h = spec['target_px']
        if width < target_w or height < target_h:
            raise ArtworkValidationError(
                f"Image is too small ({width}x{height}). Minimum allowed is {target_w}x{target_h}. "
                f"Please upload an image at least {target_w}x{target_h}."
            )
        if width > target_w + 1 or height > target_h + 1:
            raise ArtworkValidationError(
                f"Image is too large ({width}x{height}). Maximum allowed is {target_w}x{target_h}. "
                f"Please upload the documented {target_w}x{target_h} size."
            )

        if img.format not in ('JPEG', 'PNG', 'WEBP'):
            raise ArtworkValidationError(f"Unsupported format '{img.format}'. Please use JPEG, PNG, or WebP.")

    async def upload_artwork(
        self, 
        db: AsyncSession, 
        show_id: Optional[uuid.UUID], 
        show_slug: Optional[str],
        artwork_type: str, 
        file: UploadFile,
        episode_id: Optional[uuid.UUID] = None,
    ) -> Artwork:
        if artwork_type not in self.ref.get('artwork_specs', {}):
            raise ArtworkValidationError(f"Unknown artwork type '{artwork_type}'.")
            
        spec = self.ref['artwork_specs'][artwork_type]
        max_bytes = spec['max_kb'] * 1024

        # Read safely to avoid memory exhaustion
        content = bytearray()
        while True:
            chunk = await file.read(64 * 1024)
            if not chunk:
                break
            content.extend(chunk)
            if len(content) > max_bytes:
                raise ArtworkValidationError(f"File exceeds maximum allowed size of {spec['max_kb']} KB.")
        
        content_bytes = bytes(content)

        # 1. Validate
        self._validate_image(content_bytes, artwork_type)

        # 2. Extract metadata
        img = Image.open(BytesIO(content_bytes))
        width, height = img.size
        ext = 'jpg' if img.format == 'JPEG' else img.format.lower()
        mime = f"image/{ext}"

        # 3. Generate storage key
        if episode_id:
            key = f"artwork/episodes/{episode_id}/{artwork_type}.{ext}"
            lookup = select(Artwork).where(
                Artwork.episode_id == episode_id,
                Artwork.artwork_type == artwork_type,
            )
        else:
            key = f"artwork/{show_slug}/{artwork_type}.{ext}"
            lookup = select(Artwork).where(
                Artwork.show_id == show_id,
                Artwork.artwork_type == artwork_type,
            )

        # 4. Save to storage
        await self.storage.put(key, content_bytes, mime)

        # 5. Save to DB (UPSERT equivalent or manual check)
        result = await db.execute(
            lookup
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Optionally delete old file if path changed, but here they just overwrite
            if existing.storage_key != key:
                await self.storage.delete(existing.storage_key)
                
            existing.storage_key = key
            existing.original_name = file.filename
            existing.width = width
            existing.height = height
            existing.file_size = len(content_bytes)
            existing.mime_type = mime
            artwork = existing
        else:
            artwork = Artwork(
                show_id=show_id,
                episode_id=episode_id,
                artwork_type=artwork_type,
                storage_key=key,
                original_name=file.filename,
                width=width,
                height=height,
                file_size=len(content_bytes),
                mime_type=mime
            )
            db.add(artwork)
            
        await db.commit()
        await db.refresh(artwork)
        return artwork
