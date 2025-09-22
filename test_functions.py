#!/usr/bin/env python3
"""Test script to verify all main functions work correctly."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_tag_processing():
    """Test tag processing functionality with frequency support."""
    print("Testing tag processing...")
    
    # Import after adding to path
    from main import TagAutoCompleteApp
    
    # Create test DataFrame mimicking derpibooru structure
    test_data = pd.DataFrame({
        'tag': ['apple', 'banana', 'dog'],
        'category': ['0', '1', '3'],
        'frequency': ['1000', '500', '2000'],
        'alternatives': ['fruit,red', 'yellow', 'animal,pet']
    })
    
    # Create app instance to test the method
    app = TagAutoCompleteApp.__new__(TagAutoCompleteApp)
    
    # Test process_tags_with_frequency method
    result_tags, result_frequencies = app.process_tags_with_frequency(test_data)
    
    # Check that main tags are present
    assert 'apple' in result_tags, "apple should be in tags"
    assert 'banana' in result_tags, "banana should be in tags"
    assert 'dog' in result_tags, "dog should be in tags"
    
    # Check that alternative tags are present
    assert 'fruit' in result_tags, "fruit should be in alternative tags"
    assert 'animal' in result_tags, "animal should be in alternative tags"
    
    # Check frequencies
    assert result_frequencies['apple'] == 1000, f"apple frequency should be 1000, got {result_frequencies['apple']}"
    assert result_frequencies['dog'] == 2000, f"dog frequency should be 2000, got {result_frequencies['dog']}"
    
    # Check that alternatives have reduced frequency
    assert result_frequencies['fruit'] == 500, f"fruit frequency should be 500 (half of apple), got {result_frequencies['fruit']}"
    
    print("✓ Tag processing with frequency test passed")

def test_frequency_aware_matching():
    """Test the frequency-aware substring matching functionality."""
    print("Testing frequency-aware matching...")
    
    from main import TagAutoCompleteApp
    
    # Create mock app instance with frequency data based on real derpibooru patterns
    app = Mock()
    app.all_tags = [
        'safe', 'saddle', 'sadness', 'safety_first',  # starts with 'sa'
        'santa_hat', 'salad_bowl', 'sample_text',     # starts with 'sa' 
        'transparent_safe', 'unsafe_area', 'casa_blanca',  # contains 'sa'
        'design_salary', 'message_saved', 'easy_task',     # contains 'sa'
        'solo', 'smiling', 'simple_background',  # starts with 's' - high frequency
        'dog', 'cat', 'tree', 'house'  # unrelated tags
    ]
    app.all_tags_lower = [tag.lower() for tag in app.all_tags]
    
    # Frequency data simulating real derpibooru frequencies
    app.tag_frequencies = {
        'safe': 2204259,  # очень популярный тег
        'solo': 1450934,  # очень популярный тег  
        'smiling': 408347,  # популярный тег
        'simple_background': 612319,  # популярный тег
        'saddle': 5000,   # менее популярный
        'sadness': 1000,  # редкий тег
        'safety_first': 100,  # очень редкий
        'santa_hat': 50000,  # средней популярности
        'salad_bowl': 500,  # редкий
        'sample_text': 100,  # очень редкий
        'transparent_safe': 25000,  # средней популярности
        'unsafe_area': 2000,  # менее популярный
        'casa_blanca': 50,  # очень редкий
        'design_salary': 300,  # редкий
        'message_saved': 150,  # очень редкий
        'easy_task': 800,  # редкий
        'dog': 100000,  # популярный
        'cat': 80000,   # популярный
        'tree': 60000,  # популярный
        'house': 40000  # популярный
    }
    app.tag_cache = {}
    
    # Test 'sa' query - should prioritize by frequency within matching categories
    suggestions = TagAutoCompleteApp.find_suggestions(app, 'sa')
    print(f"Suggestions for 'sa': {suggestions}")
    print(f"With frequencies: {[(tag, app.tag_frequencies.get(tag, 0)) for tag in suggestions]}")
    
    # 'safe' should be first as it has highest frequency among 'sa' matches
    assert suggestions[0] == 'safe', f"'safe' should be first, got {suggestions[0]}"
    assert 'santa_hat' in suggestions, "santa_hat should be in suggestions"
    
    # Test 's' query - should show popular 's' tags first
    s_suggestions = TagAutoCompleteApp.find_suggestions(app, 's')
    print(f"Suggestions for 's': {s_suggestions}")
    print(f"With frequencies: {[(tag, app.tag_frequencies.get(tag, 0)) for tag in s_suggestions]}")
    
    # Should prioritize high-frequency tags starting with 's'
    assert 'safe' in s_suggestions, "safe should be in 's' suggestions"
    assert 'solo' in s_suggestions, "solo should be in 's' suggestions"
    
    # Test exact match prioritization
    safe_suggestions = TagAutoCompleteApp.find_suggestions(app, 'safe')
    print(f"Suggestions for 'safe': {safe_suggestions}")
    assert 'safe' == safe_suggestions[0], "Exact match 'safe' should be first"
    
    print("✓ Frequency-aware matching test passed")

def test_substring_matching():
    """Test the basic substring matching (legacy test for compatibility)."""
    print("Testing basic substring matching...")
    
    from main import TagAutoCompleteApp
    
    # Create simple mock app instance
    app = Mock()
    app.all_tags = ['safe', 'saddle', 'santa_hat', 'transparent_safe']
    app.all_tags_lower = [tag.lower() for tag in app.all_tags]
    app.tag_frequencies = {'safe': 1000, 'saddle': 500, 'santa_hat': 300, 'transparent_safe': 100}
    app.tag_cache = {}
    
    suggestions = TagAutoCompleteApp.find_suggestions(app, 'sa')
    print(f"Basic suggestions for 'sa': {suggestions}")
    
    assert 'safe' in suggestions, "safe should be in suggestions"
    assert 'saddle' in suggestions, "saddle should be in suggestions"
    assert 'santa_hat' in suggestions, "santa_hat should be in suggestions"
    
    print("✓ Basic substring matching test passed")

def test_hotkey_functions():
    """Test that hotkey functions are properly defined."""
    print("Testing hotkey functions...")
    
    from main import TagAutoCompleteApp
    
    # Check that all required methods exist
    required_methods = [
        'show_prev_image',
        'show_next_image', 
        'load_image',
        'refresh_image',
        'save_tags',
        'focus_input'
    ]
    
    for method_name in required_methods:
        assert hasattr(TagAutoCompleteApp, method_name), f"Method {method_name} not found"
    
    print("✓ Hotkey functions test passed")

def test_error_handling():
    """Test error handling for missing database."""
    print("Testing error handling...")
    
    from main import TagAutoCompleteApp
    
    # Check that error dialog methods exist
    required_dialogs = [
        '_show_missing_database_dialog',
        '_show_database_error_dialog',
        '_open_database_download_link'
    ]
    
    for dialog_name in required_dialogs:
        assert hasattr(TagAutoCompleteApp, dialog_name), f"Dialog method {dialog_name} not found"
    
    print("✓ Error handling test passed")

def test_file_structure():
    """Test that all required files are present."""
    print("Testing file structure...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'README.md',
        'LICENSE',
        '.gitignore',
        '.github/workflows/build-executable.yml',
        'ImageTagEditor.spec'
    ]
    
    for file_path in required_files:
        path = Path(file_path)
        assert path.exists(), f"Required file {file_path} not found"
    
    print("✓ File structure test passed")

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    
    try:
        import pandas as pd
        print("✓ pandas import successful")
    except ImportError as e:
        print(f"✗ pandas import failed: {e}")
        return False
    
    try:
        from PyQt6.QtWidgets import QApplication
        print("✓ PyQt6 import successful")
    except ImportError as e:
        print(f"✗ PyQt6 import failed: {e}")
        return False
    
    try:
        from main import TagAutoCompleteApp
        print("✓ Main application import successful")
    except ImportError as e:
        print(f"✗ Main application import failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("Running Image Tag Editor Function Tests")
    print("=" * 50)
    
    try:
        # Test basic imports first
        if not test_imports():
            print("\n❌ Import tests failed - cannot continue")
            return False
        
        # Run function tests
        test_tag_processing()
        test_frequency_aware_matching()
        test_substring_matching()
        test_hotkey_functions()
        test_error_handling()
        test_file_structure()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed successfully!")
        print("\nProject is ready for:")
        print("- GitHub repository upload")
        print("- Executable compilation")
        print("- Release distribution")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
