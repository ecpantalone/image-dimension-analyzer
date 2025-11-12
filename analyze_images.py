#!/usr/bin/env python3
"""
Image Dimension Analyzer
Analyzes images to find those with specific dimensions on either width or height
"""

import os
import sys
import csv
import argparse
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime
from PIL import Image
import logging
from tqdm import tqdm
import concurrent.futures
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp'}
DEFAULT_TARGET_DIMENSION = 330

def analyze_image(image_path: Path, target_dimension: int, mode: str = 'lte') -> Dict:
    """
    Analyze a single image and return its dimensions.
    
    Args:
        image_path: Path to the image file
        target_dimension: Target dimension to check against
        mode: 'lte' for less than or equal, 'exact' for exact match
        
    Returns:
        Dictionary with image information or None if error
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            
            if mode == 'lte':
                has_target_dimension = (width <= target_dimension or height <= target_dimension)
            else:
                has_target_dimension = (width == target_dimension or height == target_dimension)
            
            return {
                'filepath': str(image_path),
                'filename': image_path.name,
                'width': width,
                'height': height,
                'matches_criteria': has_target_dimension,
                'dimension_match': 'width' if width <= target_dimension else ('height' if height <= target_dimension else 'none'),
                'format': img.format,
                'mode': img.mode,
                'file_size_mb': image_path.stat().st_size / (1024 * 1024)
            }
    except Exception as e:
        logger.error(f"Error analyzing {image_path}: {e}")
        return None

def find_images(directory: Path, extensions: set = None) -> List[Path]:
    """
    Recursively find all image files in directory.
    
    Args:
        directory: Root directory to search
        extensions: Set of file extensions to include
        
    Returns:
        List of Path objects for found images
    """
    if extensions is None:
        extensions = SUPPORTED_FORMATS
    
    image_files = []
    
    for ext in extensions:
        image_files.extend(directory.rglob(f'*{ext}'))
        image_files.extend(directory.rglob(f'*{ext.upper()}'))
    
    return list(set(image_files))

def process_images(directory: Path, target_dimension: int, max_workers: int = 4, mode: str = 'lte') -> Tuple[List[Dict], List[Dict]]:
    """
    Process all images in directory using parallel processing.
    
    Args:
        directory: Root directory to search
        target_dimension: Target dimension to check against
        max_workers: Maximum number of parallel workers
        mode: 'lte' for less than or equal, 'exact' for exact match
        
    Returns:
        Tuple of (all_results, matching_results)
    """
    logger.info(f"Searching for images in {directory}")
    image_files = find_images(directory)
    logger.info(f"Found {len(image_files)} image files to analyze")
    
    all_results = []
    matching_results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_image, img, target_dimension, mode): img for img in image_files}
        
        with tqdm(total=len(image_files), desc="Analyzing images") as pbar:
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    all_results.append(result)
                    if result['matches_criteria']:
                        matching_results.append(result)
                        logger.info(f"Found match: {result['filename']} ({result['width']}x{result['height']})")
                pbar.update(1)
    
    return all_results, matching_results

def save_results(results: List[Dict], output_file: str):
    """
    Save results to CSV file.
    
    Args:
        results: List of image analysis results
        output_file: Path to output CSV file
    """
    if not results:
        logger.warning("No results to save")
        return
    
    fieldnames = ['filepath', 'filename', 'width', 'height', 'matches_criteria',
                  'dimension_match', 'format', 'mode', 'file_size_mb']
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Results saved to {output_file}")

def print_summary(all_results: List[Dict], matching_results: List[Dict], target_dimension: int, mode: str):
    """
    Print analysis summary.
    
    Args:
        all_results: All analyzed images
        matching_results: Images matching criteria
        target_dimension: Target dimension used for matching
        mode: Match mode used ('lte' or 'exact')
    """
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total images analyzed: {len(all_results)}")
    mode_symbol = '≤' if mode == 'lte' else '='
    print(f"Images matching criteria ({mode_symbol}{target_dimension}px): {len(matching_results)}")
    
    if matching_results:
        print(f"\nMatching images ({len(matching_results)}):")
        print("-"*60)
        
        dimension_stats = defaultdict(int)
        size_ranges = defaultdict(int)
        
        for result in matching_results:
            print(f"  {result['filename']}")
            print(f"    Path: {result['filepath']}")
            print(f"    Dimensions: {result['width']}x{result['height']} px")
            print(f"    Size: {result['file_size_mb']:.2f} MB")
            print()
            
            # Track which dimension matches
            if mode == 'lte':
                if result['width'] <= target_dimension:
                    dimension_stats['width'] += 1
                if result['height'] <= target_dimension:
                    dimension_stats['height'] += 1
            else:
                if result['width'] == target_dimension:
                    dimension_stats['width'] += 1
                if result['height'] == target_dimension:
                    dimension_stats['height'] += 1
        
        print("-"*60)
        print(f"Statistics:")
        mode_symbol = '≤' if mode == 'lte' else '='
        print(f"  Images with width {mode_symbol}{target_dimension}px: {dimension_stats['width']}")
        print(f"  Images with height {mode_symbol}{target_dimension}px: {dimension_stats['height']}")
    
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description='Analyze image dimensions to find images with specific dimensions')
    parser.add_argument('directory', nargs='?', default='.', 
                       help='Directory to analyze (default: current directory)')
    parser.add_argument('--output', '-o', default=None,
                       help='Output CSV file for all results')
    parser.add_argument('--matches-output', '-m', default=None,
                       help='Output CSV file for matching images only')
    parser.add_argument('--workers', '-w', type=int, default=4,
                       help='Number of parallel workers (default: 4)')
    parser.add_argument('--dimension', '-d', type=int, default=DEFAULT_TARGET_DIMENSION,
                       help=f'Target dimension to search for (default: {DEFAULT_TARGET_DIMENSION})')
    parser.add_argument('--mode', choices=['lte', 'exact'], default='lte',
                       help='Match mode: lte (less than or equal) or exact (exact match) (default: lte)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    target_dimension = args.dimension
    
    directory = Path(args.directory).resolve()
    
    if not directory.exists():
        logger.error(f"Directory {directory} does not exist")
        sys.exit(1)
    
    if not directory.is_dir():
        logger.error(f"{directory} is not a directory")
        sys.exit(1)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.output is None:
        args.output = f"image_analysis_all_{timestamp}.csv"
    
    if args.matches_output is None:
        args.matches_output = f"image_analysis_{args.dimension}px_{timestamp}.csv"
    
    logger.info(f"Starting analysis of {directory}")
    mode_desc = f"≤{target_dimension}px" if args.mode == 'lte' else f"={target_dimension}px"
    logger.info(f"Looking for images with {mode_desc} dimension")
    
    all_results, matching_results = process_images(directory, target_dimension, args.workers, args.mode)
    
    save_results(all_results, args.output)
    save_results(matching_results, args.matches_output)
    
    print_summary(all_results, matching_results, target_dimension, args.mode)
    
    logger.info("Analysis complete")

if __name__ == '__main__':
    main()