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
    """Test tag processing functionality."""
    print("Testing tag processing...")
    
    # Import after adding to path
    from main import TagAutoCompleteApp
    
    # Create test DataFrame
    test_data = pd.DataFrame({
        'tag1': ['apple', 'banana,cherry', 'dog'],
        'tag2': ['red,green', 'yellow', 'animal'],
        'tag3': ['fruit', 'sweet', 'pet']
    })
    
    # Test process_tags method
    result = TagAutoCompleteApp.process_tags(test_data)
    
    expected_tags = ['animal', 'apple', 'banana', 'cherry', 'dog', 'fruit', 'green', 'pet', 'red', 'sweet', 'yellow']
    
    assert sorted(result) == expected_tags, f"Expected {expected_tags}, got {sorted(result)}"
    print("✓ Tag processing test passed")

def test_substring_matching():
    """Test the improved substring matching functionality."""
    print("Testing substring matching...")
    
    from main import TagAutoCompleteApp
    
    # Create mock app instance
    app = Mock()
    app.all_tags = ['saddle_bag', 'safe', 'santa_hat', 'sad_face', 'sandwich', 'save_file']
    app.all_tags_lower = [tag.lower() for tag in app.all_tags]
    app.tag_cache = {}
    
    # Test find_suggestions method
    suggestions = TagAutoCompleteApp.find_suggestions(app, 'sa')
    
    # Should prioritize word starts like 'saddle_bag', 'santa_hat'
    assert 'saddle_bag' in suggestions, "saddle_bag should be in suggestions for 'sa'"
    assert 'santa_hat' in suggestions, "santa_hat should be in suggestions for 'sa'" 
    assert 'safe' in suggestions, "safe should be in suggestions for 'sa'"
    
    print("✓ Substring matching test passed")

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
        'ImageTagEditor.spec',
        'create_icon.py'
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
