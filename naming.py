"""
Non-overwriting filename utilities with random IDs.
"""

import random
import string
from pathlib import Path
from typing import Set


def generate_random_id(length: int = 6) -> str:
    """
    Generate a random alphanumeric ID.
    
    Args:
        length: Length of ID (default 6).
    
    Returns:
        Random alphanumeric string.
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def safe_output_path(
    output_dir: Path,
    base_stem: str,
    extension: str = '.png',
    existing_names: Set[str] = None,
    max_collisions: int = 100
) -> Path:
    """
    Generate a safe output path that doesn't overwrite existing files.
    Appends a random ID to the filename.
    
    Args:
        output_dir: Output directory (will be created if needed).
        base_stem: Base filename without extension.
        extension: File extension (default '.png').
        existing_names: Set of already-used names to avoid (optional).
        max_collisions: Max retries before giving up.
    
    Returns:
        A Path object pointing to a non-existent file.
    
    Raises:
        RuntimeError if collision limit reached.
    """
    if existing_names is None:
        existing_names = set()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for _ in range(max_collisions):
        random_id = generate_random_id()
        filename = f"{base_stem}_{random_id}{extension}"
        full_path = output_dir / filename
        
        if not full_path.exists() and full_path.name not in existing_names:
            existing_names.add(full_path.name)
            return full_path
    
    raise RuntimeError(
        f"Could not generate unique filename after {max_collisions} attempts "
        f"(too many collisions in {output_dir})"
    )
