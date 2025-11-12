# Image Dimension Analyzer

A high-performance Python tool for analyzing large image datasets to identify images with specific dimensions on either width or height.

## Overview

This tool provides efficient parallel processing and comprehensive reporting capabilities for dimension-based image filtering across large datasets (tested with 30+ GB of image data).

## Features

- **Parallel Processing**: Multi-threaded analysis using configurable worker pools
- **Dual Output Mode**: Generate both complete dataset analysis and filtered results
- **Real-time Progress**: Visual progress tracking with tqdm
- **Flexible Matching**: Support for exact or less-than-equal dimension matching
- **Comprehensive Logging**: Both console and file logging for debugging
- **Multi-format Support**: Handles JPG, JPEG, PNG, TIFF, TIF, BMP, GIF, WEBP
- **Memory Efficient**: Processes images individually to handle large datasets

## Installation

```bash
# Clone the repository
git clone https://github.com/ecpantalone/image-dimension-analyzer.git
cd image-dimension-analyzer

# Install dependencies
pip install -r requirements.txt
```

### Dependencies
- `Pillow` - Image processing
- `tqdm` - Progress bar visualization
- `Flask` - Web UI framework (optional, for web interface)

## Usage

You can use this tool either via command line or through a web interface.

### Command Line Usage

```bash
# Analyze a directory of images (default: 330px)
python analyze_images.py /path/to/images

# Search for images with 500px dimension
python analyze_images.py /path/to/images --dimension 500

# Search for images with exactly 200px dimension
python analyze_images.py /path/to/images --dimension 200 --mode exact
```

### Advanced Options

```bash
# Specify custom dimension and output directory
python analyze_images.py /path/to/images --dimension 800 --output-dir ./results

# Use exact dimension matching (e.g., exactly 1024px)
python analyze_images.py /path/to/images --dimension 1024 --mode exact

# Adjust number of parallel workers
python analyze_images.py /path/to/images --workers 8

# Disable filtered output (only generate complete analysis)
python analyze_images.py /path/to/images --no-filtered

# Combine multiple options
python analyze_images.py /path/to/images --dimension 150 --mode lte --workers 12
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `directory` | Path to directory containing images | Required |
| `--dimension`, `-d` | Target dimension to search for (in pixels) | 330 |
| `--output-dir` | Directory for output CSV files | Current directory |
| `--workers`, `-w` | Number of parallel workers | 4 |
| `--mode` | Matching mode: 'lte' (less than or equal) or 'exact' (exact match) | 'lte' |
| `--no-filtered` | Skip creating filtered CSV file | False |

## Output Files

The tool generates two CSV files with timestamps:

1. **`image_analysis_all_[YYYYMMDD_HHMMSS].csv`** - Complete dataset analysis
2. **`image_analysis_[dimension]px_[YYYYMMDD_HHMMSS].csv`** - Only images matching dimension criteria

For example, when searching for 500px images, the filtered file would be named `image_analysis_500px_20231115_143022.csv`.

### CSV Columns

- `file_path` - Full path to the image file
- `filename` - Name of the file
- `width` - Image width in pixels
- `height` - Image height in pixels
- `has_target_dimension` - Boolean flag for target dimension match
- `file_size_mb` - File size in megabytes

## Performance

- Default configuration uses 4 parallel workers
- Optimized for I/O-bound operations using ThreadPoolExecutor
- Memory-efficient single-image processing
- Handles corrupted/unreadable images gracefully

## Configuration

### Target Dimension
The target dimension is configurable via command-line argument. The default is 330px:

```bash
# Use default 330px
python analyze_images.py /path/to/images

# Use custom dimension
python analyze_images.py /path/to/images --dimension 768
```

### Supported Formats
Modify `SUPPORTED_FORMATS` to add or remove image formats:

```python
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp'}
```

## Logging

Logs are written to multiple destinations:
- Console output (INFO level and above)
- `image_analysis.log` file (all logs - INFO, WARNING, ERROR)
- `image_analysis_errors.log` file (ERROR level only - for quick error review)

## Testing

Run the test suite:

```bash
python test_analyze_images.py
```

The test suite includes tests for:
- Different target dimensions (200px, 330px, 500px, etc.)
- Both matching modes (lte and exact)
- Edge cases and error handling

## Project Structure

```
image-dimension-analyzer/
├── analyze_images.py         # Main analysis script
├── test_analyze_images.py    # Test suite
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── PROJECT_STATUS.md         # Development status tracking
├── .gitignore               # Git ignore file
└── image_analysis.log       # Generated log file (after first run)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Specify your license here]

## Examples

### Finding thumbnail images (≤150px)
```bash
python analyze_images.py ./media --dimension 150 --mode lte
```

### Finding HD images (exactly 1920px width or height)
```bash
python analyze_images.py ./photos --dimension 1920 --mode exact
```

### Finding mobile-optimized images (≤768px)
```bash
python analyze_images.py ./website/images --dimension 768 --workers 8
```

## Web Interface

The tool includes a web-based user interface for easier interaction.

### Starting the Web UI

```bash
# Start the Flask web server
python app.py

# The web interface will be available at http://localhost:5001
# Note: Port 5001 is used to avoid conflicts with AirPlay Receiver on macOS
```

### Web UI Features

- **Visual Interface**: User-friendly form for configuring analysis parameters
- **Directory Browser**: Browse and select directories directly from the UI
- **Real-time Progress**: Live progress updates during analysis
- **Results Dashboard**: View analysis statistics and download CSV reports
- **Recent Analyses**: Track history of recent analysis jobs
- **Background Processing**: Run multiple analyses without blocking the interface

### Web UI Screenshots

The web interface provides:
1. A clean form to input analysis parameters
2. Real-time progress tracking with percentage and statistics
3. Results summary with download options for CSV files
4. History of recent analyses with their status

### API Endpoints

If you want to integrate with the web service programmatically:

- `POST /analyze` - Start a new analysis job
- `GET /status/<job_id>` - Get status of an analysis job
- `GET /download/<job_id>/<type>` - Download results (type: 'all' or 'matching')
- `GET /recent` - Get list of recent analysis jobs
- `GET /browse?path=<path>` - Browse directories on the server

## Support

For issues or questions, please open an issue in the repository.