# CorruptGen: Artistic Image Corruption Pipeline

A Python CLI tool that loads images in any common format, converts them to JPEG with controlled compression, applies bounded corruption (with validation to ensure the output remains decodable), and exports the result as high-quality PNG. Supports single-file and folder (top-level) batch processing with non-overwriting outputs via randomized alphanumeric IDs.

## Features

- **Format Agnostic**: Loads JPG, PNG, BMP, TIFF, WebP, GIF, and more via [Pillow](https://python-pillow.org/)
- **Intelligent Corruption**: Corrupts JPEG bytes after a configurable header offset to minimize total breakage
- **Bounded Validation**: Retries corruption/decoding until the result is still loadable (or hits max attempts)
- **Safe Outputs**: Appends random 6-character alphanumeric IDs to prevent overwriting existing files
- **Batch Processing**: Recursively or top-level folder scans with per-file error handling and summary reporting
- **Reproducible**: Optional `--seed` parameter for deterministic results
- **High-Quality Export**: PNG output with tunable compression (default compress_level=3 for quality/speed balance)

## Installation

### Requirements
- Python 3.7+
- Pillow (for image handling)

### Setup

1. Clone or download the repository.
2. Install dependencies:
   ```bash
   pip install Pillow
   ```

## Usage

### Single File

```bash
python cli.py --input myimage.jpg --output-dir ./corrupted
```

Outputs: A PNG file with random ID appended, e.g., `myimage_a7Kx2Q.png`

### Folder (Top-Level Files Only)

```bash
python cli.py --input ./images --output-dir ./corrupted
```

Processes all image files in `./images` (non-recursive); outputs go to `./corrupted`.

### Custom Parameters

```bash
python cli.py \
  --input image.png \
  --output-dir ./output \
  --corruption-factor 500 \
  --header-offset 150 \
  --max-attempts 20 \
  --jpeg-quality 80 \
  --id-length 8
```

### Reproducible Results

```bash
python cli.py --input image.jpg --seed 42
```

Same `--seed` value produces identical corruption patterns across runs.

### Verbose Output

```bash
python cli.py --input image.jpg --verbose
```

Enables debug logging to trace each processing step.

## Command-Line Options

```
--input, -i                  [REQUIRED] Input file or folder
--output-dir, -o             Output directory (default: ./corrupted_output)
--corruption-factor, -c      Bytes to corrupt per attempt (default: 300)
--header-offset              Byte offset to start corruption (default: 100)
--max-attempts               Max retries for decodable result (default: 10)
--seed                       Random seed for reproducibility (optional)
--jpeg-quality               JPEG quality 1-100 (default: 85)
--id-length                  Random ID length (default: 6)
--verbose, -v                Enable debug logging
```

## Module Overview

### `cli.py`
Entry point with argparse interface. Parses arguments, validates input, and dispatches to `pipeline.py`.

### `pipeline.py`
High-level orchestration:
- `collect_image_files()`: Gathers image files from input path.
- `process_single_image()`: Load → JPEG → corrupt/validate → PNG for one file.
- `process_batch()`: Iterates over files and aggregates results.

### `processor.py`
Core image processing functions:
- `load_image()`: Opens any format and normalizes to RGB.
- `to_jpeg_bytes()`: Encodes as JPEG with quality control.
- `corrupt_bytes()`: Mutates random bytes after header offset.
- `decode_validate()`: Attempts to decode JPEG bytes (returns None if it fails).
- `corrupt_and_validate()`: Retry loop to produce decodable corruption.
- `save_png()`: Encodes final result as PNG.

### `naming.py`
Non-overwriting filename utilities:
- `generate_random_id()`: Creates random alphanumeric string.
- `safe_output_path()`: Generates collision-free output filename with random ID.

### `example.py`
Legacy wrapper for backward compatibility. Provides the original `corrupt_image()` function but recommends using the modern CLI pipeline.

## Processing Pipeline

1. **Load**: Read input file (any format) and normalize to RGB.
2. **JPEG Conversion**: Encode as JPEG with specified quality (default 85).
3. **Corruption & Validation** (up to `--max-attempts` times):
   - Corrupt JPEG bytes after `--header-offset`.
   - Attempt to decode the corrupted JPEG.
   - If successful, proceed to PNG export; otherwise retry.
4. **PNG Export**: Encode final decoded image as high-quality PNG (compress_level 3).
5. **Safe Naming**: Append random ID to output filename; skip if file already exists.

## Batch Summary Report

After processing, the tool prints:

```
============================================================
Summary:
  Processed:  10
  Succeeded:  9
  Failed:     1
  Skipped:    0
  Ended:      2026-02-24 14:32:15

Errors:
  • ./images/broken.jpg: Failed to load image from ./images/broken.jpg: cannot identify image file
============================================================
```

Exit code is 0 if all succeeded; 1 if any failed.

## Output Folder Structure

### Single File Input
```
myimage.jpg  →  output/myimage_a7Kx2Q.png
```

### Folder Input
```
./images/
  ├─ photo1.jpg  →  ./corrupted/photo1_kL9oP3.png
  ├─ photo2.png  →  ./corrupted/photo2_mRx8Yz.png
  └─ document.txt (ignored)
```

## Examples

### Basic Glitch Art

```bash
python cli.py --input portrait.jpg --output-dir ./glitched
```

Produces `portrait_xxxxxx.png` with ~300 bytes corrupted.

### Heavy Corruption

```bash
python cli.py --input image.jpg --corruption-factor 1000 --max-attempts 15
```

Corrupts 1000 bytes per retry, up to 15 attempts.

### Archive Processing

```bash
python cli.py --input ./my_photos --output-dir ./glitched_archive
```

Batch processes all images in the folder, skipping non-images.

### Deterministic Batch

```bash
python cli.py --input ./test_images --seed 12345 --verbose
```

All files corrupted identically (given same input); debug output shown.

## Error Handling

- **Invalid input path**: Tool exits with error message.
- **File too small**: Skipped with warning; continues processing.
- **Undecodable after max attempts**: Logged as failure; batch continues.
- **Permission errors**: Caught and reported per-file; batch continues.

Exit code reflects overall success (0) or any failure (1).

## Performance Notes

- **Single file**: Typically <1 second (depends on image size and max_attempts).
- **Batch**: Linear with number of files; typical folder (100 images) ~30–60 seconds.
- **Memory**: Entire file loaded into memory; large files (>1GB) may be slow.

## Troubleshooting

### `ImportError: No module named 'PIL'`
Install Pillow: `pip install Pillow`

### `Image is too small to corrupt safely`
Input file smaller than `--header-offset`. Increase `--header-offset` or use smaller value, or ensure input images are large enough.

### `Failed to produce decodable corruption`
Increase `--max-attempts` or reduce `--corruption-factor`. Some files may not support many retries depending on JPEG structure.

### Output not created (but no error)
Check that `--output-dir` is writable and has space. Verify input images are recognized (try with a PNG or JPG).

## License

Open source. Modify and redistribute as needed.

## Future Enhancements

- [ ] Recursive folder traversal option.
- [ ] Alternative corruption modes (pixel-domain, frequency-domain).
- [ ] Configurable output naming (e.g., timestamp, counter).
- [ ] Parallel/async batch processing.
- [ ] Web UI for interactive testing.
