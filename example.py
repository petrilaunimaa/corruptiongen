"""
Legacy wrapper for backward compatibility.
New code should use cli.py or pipeline.py directly.
"""

from pathlib import Path
from processor import load_image, to_jpeg_bytes, corrupt_and_validate, save_png
from naming import safe_output_path
import random


def corrupt_image(input_path, output_path, corruption_factor, header_offset=100):
    """
    Legacy function: corrupt raw image bytes and save directly.
    
    NOTE: This is the original low-level interface.
    For production use, prefer the pipeline.py workflow which adds:
    - Format validation and conversion through PIL
    - JPEG encoding with quality control
    - Corruption validation (bounded retries until decodable)
    - Output as high-quality PNG
    
    Args:
        input_path: Path to input file.
        output_path: Path to output file (will be overwritten).
        corruption_factor: Number of bytes to corrupt.
        header_offset: Bytes to skip at header (default 100).
    """
    with open(input_path, 'rb') as f:
        image_data = bytearray(f.read())
        
    file_size = len(image_data)
    
    if file_size <= header_offset:
        print("Image is too small to corrupt safely.")
        return

    for _ in range(corruption_factor):
        random_index = random.randint(header_offset, file_size - 1)
        image_data[random_index] = random.randint(0, 255)
            
    with open(output_path, 'wb') as f:
        f.write(image_data)
        
    print(f"Successfully corrupted {corruption_factor} bytes and saved to {output_path}")


# Example Usage:
# This will modify 300 random bytes in 'test.jpg' and output 'glitched.jpg'
# corrupt_image('test.jpg', 'glitched.jpg', corruption_factor=300, header_offset=150)

# For modern usage, see cli.py:
# python cli.py --input test.jpg --output-dir ./output --corruption-factor 300