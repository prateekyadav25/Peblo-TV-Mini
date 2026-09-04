import os
from io import BytesIO
import pytest
from PIL import Image
from app.services.artwork_service import ArtworkService, ArtworkValidationError
from app.storage.local import LocalStorageBackend

@pytest.fixture
def storage():
    # Use a temp directory for storage
    return LocalStorageBackend(base_path="/tmp/peblo_storage_test")

@pytest.fixture
def artwork_service(storage):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    ref_path = os.path.join(root_dir, 'reference.json')
    return ArtworkService(storage, ref_path)

def image_bytes(width: int, height: int, image_format: str = "JPEG") -> bytes:
    image = Image.new("RGB", (width, height), (32, 64, 96))
    output = BytesIO()
    image.save(output, format=image_format, quality=30, optimize=True)
    return output.getvalue()

def test_valid_poster(artwork_service):
    content = image_bytes(600, 900)
    artwork_service._validate_image(content, 'poster')
    # Should not raise any exception

def test_wrong_ratio_poster(artwork_service):
    content = image_bytes(600, 600)
    with pytest.raises(ArtworkValidationError) as exc_info:
        artwork_service._validate_image(content, 'poster')
    assert "must be 2:3" in str(exc_info.value)

def test_tiny_thumbnail(artwork_service):
    content = image_bytes(320, 180)
    with pytest.raises(ArtworkValidationError) as exc_info:
        artwork_service._validate_image(content, 'thumbnail')
    assert "too small" in str(exc_info.value).lower()

def test_valid_banner(artwork_service):
    content = image_bytes(1280, 720)
    artwork_service._validate_image(content, 'banner')

def test_banner_too_big(artwork_service):
    content = image_bytes(1282, 721)
    with pytest.raises(ArtworkValidationError) as exc_info:
        artwork_service._validate_image(content, 'banner')
    assert "too large" in str(exc_info.value).lower()

def test_valid_thumbnail(artwork_service):
    content = image_bytes(640, 360)
    artwork_service._validate_image(content, 'thumbnail')

def test_corrupt_image(artwork_service):
    content = b"Not a real image file."
    with pytest.raises(ArtworkValidationError) as exc_info:
        artwork_service._validate_image(content, 'poster')
    assert "Unsupported or corrupt image" in str(exc_info.value)

def test_oversized_file(artwork_service):
    # Simulate an oversized file by appending junk to a valid image
    # Note: Pillow might still open it, but our size check runs first!
    content = image_bytes(600, 900)
    large_content = content + (b"0" * (300 * 1024)) # Add 300KB
    with pytest.raises(ArtworkValidationError) as exc_info:
        artwork_service._validate_image(large_content, 'poster')
    assert "Maximum allowed is 200 KB" in str(exc_info.value)
