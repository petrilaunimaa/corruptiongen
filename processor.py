"""
Image processing pipeline: load, corrupt, validate, save.
"""

import random
import io
from pathlib import Path
from typing import Tuple, Optional

try:
    from PIL import Image
    from PIL import ImageFile
except ImportError as e:
    raise ImportError("Pillow is required. Install with: pip install Pillow") from e


ImageFile.LOAD_TRUNCATED_IMAGES = True


def load_image(input_path: str) -> Image.Image:
    """
    Load any image format and return a PIL Image object.
    Normalizes RGBA/palette modes to RGB if needed.
    
    Args:
        input_path: Path to input image file.
    
    Returns:
        PIL Image object.
    
    Raises:
        Exception if file cannot be decoded.
    """
    try:
        img = Image.open(input_path)
        # Convert RGBA, palette, or other modes to RGB for consistent handling
        if img.mode in ('RGBA', 'LA', 'P', 'CMYK'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            return rgb_img
        elif img.mode != 'RGB':
            return img.convert('RGB')
        return img
    except Exception as e:
        raise Exception(f"Failed to load image from {input_path}: {e}") from e


def to_jpeg_bytes(img: Image.Image, quality: int = 85, optimize: bool = True) -> bytes:
    """
    Encode PIL Image to JPEG bytes with specified quality.
    
    Args:
        img: PIL Image object (expected RGB or compatible).
        quality: JPEG quality (1-100, default 85).
        optimize: Whether to optimize JPEG encoding.
    
    Returns:
        JPEG bytes.
    """
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=optimize)
    return buffer.getvalue()


def corrupt_bytes(data: bytearray, corruption_factor: int, header_offset: int = 100) -> bytearray:
    """
    Corrupt random bytes in a bytearray after a safe header offset.
    
    Args:
        data: Mutable bytearray to corrupt.
        corruption_factor: Number of bytes to corrupt.
        header_offset: Number of bytes to skip at start (header protection).
    
    Returns:
        Modified bytearray.
    
    Raises:
        ValueError if file is too small or corruption_factor is invalid.
    """
    if len(data) <= header_offset + 2:
        raise ValueError(f"File too small ({len(data)} bytes) for header_offset={header_offset}")
    if corruption_factor <= 0:
        raise ValueError(f"corruption_factor must be > 0, got {corruption_factor}")
    
    # Limit corruption to available space
    max_corruptible = len(data) - header_offset - 2
    actual_factor = min(corruption_factor, max_corruptible)
    
    for _ in range(actual_factor):
        random_index = random.randint(header_offset, len(data) - 3)
        replacement = random.randint(0, 254)
        if replacement == data[random_index]:
            replacement = (replacement + 1) % 255
        data[random_index] = replacement
    
    return data


def decode_validate(jpeg_bytes: bytes) -> Optional[Image.Image]:
    """
    Attempt to decode and validate JPEG bytes.
    
    Args:
        jpeg_bytes: Raw JPEG bytes.
    
    Returns:
        PIL Image if successful, None if decode fails.
    """
    try:
        img = Image.open(io.BytesIO(jpeg_bytes))
        img.load()  # Force full decode
        return img
    except Exception:
        return None


def save_png(img: Image.Image, output_path: str, compress_level: int = 3) -> None:
    """
    Save PIL Image as high-quality PNG.
    
    Args:
        img: PIL Image object.
        output_path: Path to save PNG.
        compress_level: PNG compression (0-9, default 3 for speed/quality balance).
    """
    img.save(output_path, format='PNG', compress_level=compress_level, optimize=True)


def corrupt_and_validate(
    jpeg_bytes: bytes,
    corruption_factor: int,
    header_offset: int = 100,
    max_attempts: int = 10,
    seed: Optional[int] = None,
    min_corruption_factor: int = 1
) -> Tuple[Optional[Image.Image], int]:
    """
    Corrupt JPEG bytes with bounded retries until result is decodable.
    
    Args:
        jpeg_bytes: Original JPEG file bytes.
        corruption_factor: Number of bytes to corrupt per attempt.
        header_offset: Header protection offset.
        max_attempts: Maximum retry attempts.
        seed: Optional random seed for reproducibility.
    
    Returns:
        Tuple of (decoded Image if successful else None, attempts_used).
    """
    if seed is not None:
        random.seed(seed)
    
    for attempt in range(max_attempts):
        current_factor = max(
            min_corruption_factor,
            int(corruption_factor * (0.7 ** attempt))
        )
        corrupted = bytearray(jpeg_bytes)
        try:
            corrupt_bytes(corrupted, current_factor, header_offset)
        except ValueError:
            # File too small, return original decode
            return decode_validate(jpeg_bytes), attempt + 1
        
        decoded = decode_validate(bytes(corrupted))
        if decoded is not None:
            return decoded, attempt + 1
    
    # Failed after max_attempts; return None to signal failure
    return None, max_attempts
