"""
File/folder dispatch and batch processing pipeline.
"""

from pathlib import Path
from typing import List, Tuple, Optional
import logging

from processor import load_image, to_jpeg_bytes, corrupt_and_validate, save_png
from naming import safe_output_path

logger = logging.getLogger(__name__)

# Common image extensions
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif'}


def collect_image_files(input_path: str) -> List[Path]:
    """
    Collect image files from input path.
    If input is a single file, return it if valid.
    If input is a folder, list top-level files only (non-recursive).
    
    Args:
        input_path: File or folder path.
    
    Returns:
        List of Path objects pointing to valid image files.
    """
    path = Path(input_path)
    
    if not path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return []
    
    if path.is_file():
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            return [path]
        else:
            logger.warning(f"File not recognized as image: {path}")
            return []
    
    # Folder mode: top-level only
    if path.is_dir():
        files = []
        for file in path.iterdir():
            if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(file)
        return files
    
    return []


def process_single_image(
    input_file: Path,
    output_dir: Path,
    corruption_factor: int = 300,
    header_offset: int = 100,
    max_attempts: int = 10,
    seed: Optional[int] = None,
    jpeg_quality: int = 85,
    id_length: int = 6
) -> Tuple[bool, Optional[Path], str]:
    """
    Process a single image: load → JPG → corrupt/validate → PNG.
    
    Args:
        input_file: Path to input image file.
        output_dir: Output directory for PNG.
        corruption_factor: Bytes to corrupt per attempt.
        header_offset: Header protection offset.
        max_attempts: Max retry attempts for corruption validation.
        seed: Random seed for reproducibility.
        jpeg_quality: JPEG quality (1-100).
        id_length: Length of random ID appended to output filename.
    
    Returns:
        Tuple of (success: bool, output_path: Optional[Path], message: str).
    """
    try:
        # Load input image
        img = load_image(str(input_file))
        logger.debug(f"Loaded: {input_file}")
        
        # Convert to JPEG bytes
        jpeg_bytes = to_jpeg_bytes(img, quality=jpeg_quality)
        logger.debug(f"Converted to JPEG ({len(jpeg_bytes)} bytes)")
        
        # Corrupt and validate with bounded retries
        decoded_img, attempts_used = corrupt_and_validate(
            jpeg_bytes,
            corruption_factor=corruption_factor,
            header_offset=header_offset,
            max_attempts=max_attempts,
            seed=seed
        )
        
        if decoded_img is None:
            msg = (
                f"Failed to produce decodable corruption after {attempts_used} attempts "
                f"(file too small or all attempts produced undecodable JPEG)"
            )
            logger.warning(f"{input_file}: {msg}")
            return False, None, msg
        
        logger.debug(f"Corruption successful after {attempts_used} attempt(s)")
        
        # Generate safe output path with random ID
        base_stem = input_file.stem
        output_path = safe_output_path(
            output_dir,
            base_stem,
            extension='.png',
            max_collisions=100
        )
        
        # Save as PNG
        save_png(decoded_img, str(output_path))
        logger.info(f"Saved: {output_path}")
        
        return True, output_path, "Success"
    
    except Exception as e:
        msg = f"Error processing {input_file}: {e}"
        logger.error(msg)
        return False, None, msg


def process_batch(
    input_path: str,
    output_dir: str,
    corruption_factor: int = 300,
    header_offset: int = 100,
    max_attempts: int = 10,
    seed: Optional[int] = None,
    jpeg_quality: int = 85,
    id_length: int = 6,
    verbose: bool = False
) -> Tuple[int, int, int, int, List[Tuple[str, str]]]:
    """
    Process files from input (single file or folder).
    Returns summary and error log.
    
    Args:
        input_path: Input file or folder.
        output_dir: Output folder.
        corruption_factor: Bytes to corrupt per attempt.
        header_offset: Header protection offset.
        max_attempts: Max retry attempts.
        seed: Random seed.
        jpeg_quality: JPEG quality (1-100).
        id_length: Random ID length.
        verbose: Enable debug logging.
    
    Returns:
        Tuple of (processed, succeeded, failed, skipped, errors_list).
        errors_list contains (input_filename, error_message) tuples.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    files = collect_image_files(input_path)
    processed = len(files)
    succeeded = 0
    failed = 0
    skipped = 0
    errors = []
    
    if not files:
        logger.warning(f"No image files found in {input_path}")
        return 0, 0, 0, 0, []
    
    for input_file in files:
        success, output_file, message = process_single_image(
            input_file,
            output_path,
            corruption_factor=corruption_factor,
            header_offset=header_offset,
            max_attempts=max_attempts,
            seed=seed,
            jpeg_quality=jpeg_quality,
            id_length=id_length
        )
        
        if success:
            succeeded += 1
        else:
            failed += 1
            errors.append((str(input_file), message))
    
    return processed, succeeded, failed, skipped, errors
