#!/usr/bin/env python3
"""
Tests for the Image Dimension Analyzer
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import csv
import sys
import os

# Add parent directory to path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_images import (
    analyze_image,
    find_images,
    process_images,
    save_results,
    SUPPORTED_FORMATS,
    DEFAULT_TARGET_DIMENSION
)

class TestImageAnalyzer(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Create temporary test directory and test images"""
        cls.test_dir = Path(tempfile.mkdtemp(prefix="test_images_"))
        
        # Create test images with various dimensions
        cls.test_images = {
            'small_both.jpg': (200, 150),       # Both dimensions ≤330
            'exact_width.png': (330, 500),      # Width exactly 330
            'exact_height.jpg': (400, 330),     # Height exactly 330
            'small_width.png': (250, 400),      # Only width ≤330
            'small_height.jpg': (500, 200),     # Only height ≤330
            'large_both.png': (800, 600),       # Both dimensions >330
            'tiny.jpg': (50, 50),               # Very small image
            'exact_square.png': (330, 330),     # Square at exactly 330
        }
        
        # Create actual image files
        for filename, (width, height) in cls.test_images.items():
            img = Image.new('RGB', (width, height), color='red')
            img.save(cls.test_dir / filename)
        
        # Create subdirectory with more images
        cls.sub_dir = cls.test_dir / 'subdirectory'
        cls.sub_dir.mkdir()
        
        sub_image = Image.new('RGB', (100, 100), color='blue')
        sub_image.save(cls.sub_dir / 'sub_image.jpg')
        
        # Create an image with uppercase extension
        upper_image = Image.new('RGB', (300, 300), color='green')
        upper_image.save(cls.test_dir / 'upper_case.JPG')
    
    @classmethod
    def tearDownClass(cls):
        """Remove temporary test directory"""
        shutil.rmtree(cls.test_dir)
    
    def test_analyze_image_lte_mode(self):
        """Test analyzing single image in less-than-or-equal mode"""
        # Test image that should match (small dimensions)
        small_path = self.test_dir / 'small_both.jpg'
        result = analyze_image(small_path, target_dimension=330, mode='lte')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['width'], 200)
        self.assertEqual(result['height'], 150)
        self.assertTrue(result['matches_criteria'])
        self.assertEqual(result['filename'], 'small_both.jpg')
        
        # Test image that shouldn't match (large dimensions)
        large_path = self.test_dir / 'large_both.png'
        result = analyze_image(large_path, target_dimension=330, mode='lte')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['width'], 800)
        self.assertEqual(result['height'], 600)
        self.assertFalse(result['matches_criteria'])
    
    def test_analyze_image_exact_mode(self):
        """Test analyzing single image in exact match mode"""
        # Test image with exact width match
        exact_width_path = self.test_dir / 'exact_width.png'
        result = analyze_image(exact_width_path, target_dimension=330, mode='exact')
        
        self.assertIsNotNone(result)
        self.assertTrue(result['matches_criteria'])
        
        # Test image with no exact match
        small_path = self.test_dir / 'small_both.jpg'
        result = analyze_image(small_path, target_dimension=330, mode='exact')
        
        self.assertIsNotNone(result)
        self.assertFalse(result['matches_criteria'])
    
    def test_find_images(self):
        """Test finding all images in directory"""
        images = find_images(self.test_dir)
        
        # Should find all created test images including subdirectory
        # 8 in main dir + 1 in subdir + 1 uppercase = 10 total
        self.assertEqual(len(images), 10)
        
        # Check that all expected files are found
        filenames = {img.name for img in images}
        for test_file in self.test_images.keys():
            self.assertIn(test_file, filenames)
        
        # Check uppercase extension is found
        self.assertIn('upper_case.JPG', filenames)
        
        # Check subdirectory image is found
        self.assertIn('sub_image.jpg', filenames)
    
    def test_find_images_with_specific_extensions(self):
        """Test finding images with specific extensions only"""
        # Only find JPG files
        jpg_only = find_images(self.test_dir, extensions={'.jpg'})
        jpg_names = {img.name for img in jpg_only}
        
        # Should find .jpg files and uppercase .JPG
        self.assertIn('small_both.jpg', jpg_names)
        self.assertIn('upper_case.JPG', jpg_names)
        self.assertNotIn('exact_width.png', jpg_names)
    
    def test_process_images_lte_mode(self):
        """Test processing multiple images in less-than-or-equal mode"""
        all_results, matching_results = process_images(self.test_dir, target_dimension=330, max_workers=2, mode='lte')
        
        # Should process all 10 images
        self.assertEqual(len(all_results), 10)
        
        # Count images that should match (≤330px on at least one dimension)
        # All except 'large_both.png' should match
        self.assertEqual(len(matching_results), 9)
        
        # Verify large_both.png is not in matching results
        matching_names = {r['filename'] for r in matching_results}
        self.assertNotIn('large_both.png', matching_names)
    
    def test_process_images_exact_mode(self):
        """Test processing multiple images in exact match mode"""
        all_results, matching_results = process_images(self.test_dir, target_dimension=330, max_workers=2, mode='exact')
        
        # Should process all 10 images
        self.assertEqual(len(all_results), 10)
        
        # Count images with exactly 330px dimension
        # exact_width.png, exact_height.jpg, exact_square.png
        self.assertEqual(len(matching_results), 3)
        
        matching_names = {r['filename'] for r in matching_results}
        self.assertIn('exact_width.png', matching_names)
        self.assertIn('exact_height.jpg', matching_names)
        self.assertIn('exact_square.png', matching_names)
    
    def test_save_results(self):
        """Test saving results to CSV file"""
        # Create sample results
        results = [
            {
                'filepath': '/test/path/image1.jpg',
                'filename': 'image1.jpg',
                'width': 300,
                'height': 200,
                'matches_criteria': True,
                'dimension_match': 'both',
                'format': 'JPEG',
                'mode': 'RGB',
                'file_size_mb': 0.5
            },
            {
                'filepath': '/test/path/image2.png',
                'filename': 'image2.png',
                'width': 500,
                'height': 400,
                'matches_criteria': False,
                'dimension_match': 'none',
                'format': 'PNG',
                'mode': 'RGBA',
                'file_size_mb': 1.2
            }
        ]
        
        # Save to temporary file
        output_file = self.test_dir / 'test_output.csv'
        save_results(results, str(output_file))
        
        # Read back and verify
        self.assertTrue(output_file.exists())
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['filename'], 'image1.jpg')
        self.assertEqual(rows[0]['width'], '300')
        self.assertEqual(rows[0]['matches_criteria'], 'True')
        
        self.assertEqual(rows[1]['filename'], 'image2.png')
        self.assertEqual(rows[1]['width'], '500')
        self.assertEqual(rows[1]['matches_criteria'], 'False')
    
    def test_empty_directory(self):
        """Test handling of directory with no images"""
        empty_dir = self.test_dir / 'empty'
        empty_dir.mkdir()
        
        all_results, matching_results = process_images(empty_dir, target_dimension=330)
        
        self.assertEqual(len(all_results), 0)
        self.assertEqual(len(matching_results), 0)
        
        # Clean up
        empty_dir.rmdir()
    
    def test_corrupted_image(self):
        """Test handling of corrupted image file"""
        # Create a fake "image" file with invalid data
        corrupted_path = self.test_dir / 'corrupted.jpg'
        with open(corrupted_path, 'w') as f:
            f.write("This is not a valid image")
        
        result = analyze_image(corrupted_path, target_dimension=330)
        
        # Should return None for corrupted images
        self.assertIsNone(result)
        
        # Clean up
        corrupted_path.unlink()
    
    def test_dimension_edge_cases(self):
        """Test edge cases for dimension matching"""
        # Test image at exactly 330px
        exact_path = self.test_dir / 'exact_square.png'
        
        # In lte mode, should match
        result_lte = analyze_image(exact_path, target_dimension=330, mode='lte')
        self.assertTrue(result_lte['matches_criteria'])
        
        # In exact mode, should also match
        result_exact = analyze_image(exact_path, target_dimension=330, mode='exact')
        self.assertTrue(result_exact['matches_criteria'])
        
        # Test image at 331px (just over threshold)
        over_threshold = Image.new('RGB', (331, 331), color='yellow')
        over_path = self.test_dir / 'over_threshold.jpg'
        over_threshold.save(over_path)
        
        result_over = analyze_image(over_path, target_dimension=330, mode='lte')
        self.assertFalse(result_over['matches_criteria'])
        
        # Clean up
        over_path.unlink()

    def test_custom_dimension(self):
        """Test using custom target dimensions"""
        # Test with dimension=200
        all_results, matching_results = process_images(self.test_dir, target_dimension=200, mode='lte')
        
        # Images ≤200px: small_both.jpg, tiny.jpg, sub_image.jpg
        matching_names = {r['filename'] for r in matching_results}
        self.assertIn('small_both.jpg', matching_names)  # 200x150
        self.assertIn('tiny.jpg', matching_names)        # 50x50
        self.assertIn('sub_image.jpg', matching_names)   # 100x100
        
        # Test with dimension=500 exact mode
        all_results, matching_results = process_images(self.test_dir, target_dimension=500, mode='exact')
        matching_names = {r['filename'] for r in matching_results}
        self.assertIn('exact_width.png', matching_names)  # 330x500 (height=500)
        self.assertIn('small_height.jpg', matching_names) # 500x200 (width=500)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow"""
    
    def setUp(self):
        """Create test environment"""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_integration_"))
        
        # Create a realistic directory structure
        (self.test_dir / 'products' / 'shoes').mkdir(parents=True)
        (self.test_dir / 'products' / 'apparel').mkdir(parents=True)
        (self.test_dir / 'thumbnails').mkdir()
        
        # Create various test images
        test_structure = {
            'products/shoes/shoe1.jpg': (300, 300),
            'products/shoes/shoe2.png': (250, 400),
            'products/apparel/shirt1.jpg': (800, 800),
            'products/apparel/shirt2.png': (330, 330),
            'thumbnails/thumb1.jpg': (100, 100),
            'thumbnails/thumb2.png': (150, 150),
            'logo.png': (200, 50),
        }
        
        for path_str, (width, height) in test_structure.items():
            img = Image.new('RGB', (width, height), color='blue')
            img.save(self.test_dir / path_str)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_full_workflow(self):
        """Test the complete image analysis workflow"""
        # Process all images
        all_results, matching_results = process_images(self.test_dir, target_dimension=330, mode='lte')
        
        # Should find all 7 images
        self.assertEqual(len(all_results), 7)
        
        # Images ≤330px: all except shirt1.jpg
        self.assertEqual(len(matching_results), 6)
        
        # Save results
        all_output = self.test_dir / 'all_results.csv'
        matches_output = self.test_dir / 'matches.csv'
        
        save_results(all_results, str(all_output))
        save_results(matching_results, str(matches_output))
        
        self.assertTrue(all_output.exists())
        self.assertTrue(matches_output.exists())
        
        # Verify CSV contents
        with open(all_output, 'r') as f:
            all_rows = list(csv.DictReader(f))
        
        with open(matches_output, 'r') as f:
            match_rows = list(csv.DictReader(f))
        
        self.assertEqual(len(all_rows), 7)
        self.assertEqual(len(match_rows), 6)
        
        # Verify that shirt1.jpg is not in matches
        match_filenames = {row['filename'] for row in match_rows}
        self.assertNotIn('shirt1.jpg', match_filenames)

if __name__ == '__main__':
    unittest.main()