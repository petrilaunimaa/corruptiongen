#!/usr/bin/env python3
"""
CorruptGen CLI: Load any image, convert to JPG, corrupt it, and save as high-quality PNG.
Supports single files and folder (top-level only) processing.
Non-overwriting by default (random alphanumeric IDs appended to outputs).
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

from pipeline import process_batch

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='CorruptGen: corrupt images with validation and quality output.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single image
  python cli.py --input image.jpg --output-dir ./corrupted

  # Process entire folder (top-level files only)
  python cli.py --input ./images --output-dir ./corrupted

  # Custom corruption and retries
  python cli.py --input image.png --corruption-factor 500 --max-attempts 20

  # Reproducible results with seed
  python cli.py --input image.jpg --seed 42

  # Verbose output
  python cli.py --input image.jpg --verbose
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input file or folder (supports JPG, PNG, BMP, TIFF, WebP, GIF, etc.)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        default=None,
        help='Output directory (default: ./corrupted_output)'
    )
    
    parser.add_argument(
        '--corruption-factor', '-c',
        type=int,
        default=300,
        help='Number of bytes to corrupt per attempt (default: 300)'
    )
    
    parser.add_argument(
        '--header-offset',
        type=int,
        default=100,
        help='Number of bytes to skip at file header (default: 100)'
    )
    
    parser.add_argument(
        '--max-attempts',
        type=int,
        default=10,
        help='Max retry attempts to produce decodable corruption (default: 10)'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility (optional)'
    )
    
    parser.add_argument(
        '--jpeg-quality',
        type=int,
        default=85,
        choices=range(1, 101),
        metavar='1-100',
        help='JPEG quality (default: 85)'
    )
    
    parser.add_argument(
        '--id-length',
        type=int,
        default=6,
        help='Length of random ID appended to outputs (default: 6)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Set default output directory if not provided
    if args.output_dir is None:
        args.output_dir = './corrupted_output'
    
    # Validate input path exists
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input path does not exist: {args.input}")
        sys.exit(1)
    
    # Run batch processing
    print(f"\n{'='*60}")
    print(f"CorruptGen Pipeline Started")
    print(f"{'='*60}")
    print(f"Input:              {args.input}")
    print(f"Output Directory:   {args.output_dir}")
    print(f"Corruption Factor:  {args.corruption_factor}")
    print(f"Max Attempts:       {args.max_attempts}")
    print(f"Header Offset:      {args.header_offset}")
    print(f"JPEG Quality:       {args.jpeg_quality}")
    if args.seed is not None:
        print(f"Random Seed:        {args.seed}")
    print(f"Started:            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    processed, succeeded, failed, skipped, errors = process_batch(
        input_path=args.input,
        output_dir=args.output_dir,
        corruption_factor=args.corruption_factor,
        header_offset=args.header_offset,
        max_attempts=args.max_attempts,
        seed=args.seed,
        jpeg_quality=args.jpeg_quality,
        id_length=args.id_length,
        verbose=args.verbose
    )
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Processed:  {processed}")
    print(f"  Succeeded:  {succeeded}")
    print(f"  Failed:     {failed}")
    print(f"  Skipped:    {skipped}")
    print(f"  Ended:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if errors:
        print(f"\nErrors:")
        for filename, error_msg in errors:
            print(f"  • {filename}: {error_msg}")
    
    print(f"{'='*60}\n")
    
    # Exit code: 0 if all succeeded or were skipped, 1 if any failed
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
