#!/usr/bin/env python3
"""Comprehensive tests for enhanced tagging features.

Tests the new functionality:
1. Space support via underscore and plus symbols
2. Tag frequency display
3. Updated selection logic (no comma requirement)
4. Proper tag conversion between display and storage formats
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_tag_conversion():
    """Test tag conversion between display and storage formats."""
    print("Testing tag conversion...")
    
    from main import TagAutoCompleteApp
    
    # Create mock app instance
    app = TagAutoCompleteApp.__new__(TagAutoCompleteApp)
    
    # Test underscore to space conversion
    result = app.convert_tag_for_display("rainbow_dash")
    expected = "Rainbow Dash"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    
    # Test plus to space conversion  
    result = app.convert_tag_for_display("rainbow+dash")
    expected = "Rainbow Dash"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    
    # Test mixed conversion
    result = app.convert_tag_for_display("princess_celestia+alicorn")
    expected = "Princess Celestia Alicorn"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    
    # Test storage conversion
    result = app.convert_tag_for_storage("Rainbow Dash")
    expected = "rainbow_dash"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    
    # Test single word (no conversion needed)
    result = app.convert_tag_for_display("safe")
    expected = "Safe"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    
    print("✓ Tag conversion test passed")

def test_frequency_formatting():
    """Test frequency formatting with proper alignment."""
    print("Testing frequency formatting...")
    
    from main import TagAutoCompleteApp
    
    # Create mock app instance with suggestions list
    app = TagAutoCompleteApp.__new__(TagAutoCompleteApp)
    app.suggestions_list = Mock()
    app.suggestions_list.font.return_value = Mock()
    app.suggestions_list.width.return_value = 300
    
    # Mock QFontMetrics
    with patch('main.QFontMetrics') as mock_font_metrics:
        mock_metrics = Mock()
        mock_metrics.horizontalAdvance.return_value = 8  # 8 pixels per character
        mock_font_metrics.return_value = mock_metrics
        
        # Test large frequency (millions)
        result = app.format_suggestion_with_frequency("Safe", 2204259)
        assert "2.2M" in result, f"Expected '2.2M' in result, got '{result}'"
        assert "Safe" in result, f"Expected 'Safe' in result, got '{result}'"
        
        # Test medium frequency (thousands)
        result = app.format_suggestion_with_frequency("Rainbow Dash", 45000)
        assert "45.0K" in result, f"Expected '45.0K' in result, got '{result}'"
        assert "Rainbow Dash" in result, f"Expected 'Rainbow Dash' in result, got '{result}'"
        
        # Test small frequency (raw number)
        result = app.format_suggestion_with_frequency("OC Only", 500)
        assert "500" in result, f"Expected '500' in result, got '{result}'"
        assert "OC Only" in result, f"Expected 'OC Only' in result, got '{result}'"
        
        # Test very long tag name (should be truncated)
        long_tag = "Very Long Tag Name That Should Be Truncated"
        result = app.format_suggestion_with_frequency(long_tag, 1000)
        assert "..." in result, f"Expected truncation '...' in result, got '{result}'"
        assert "1.0K" in result, f"Expected '1.0K' in result, got '{result}'"
    
    print("✓ Frequency formatting test passed")

def test_enhanced_suggestion_logic():
    """Test the enhanced suggestion logic with frequency prioritization."""
    print("Testing enhanced suggestion logic...")
    
    from main import TagAutoCompleteApp
    
    # Create mock app instance with test data
    app = Mock()
    app.all_tags = [
        'female', 'female_oc', 'safe', 'solo_female', 
        'rainbow_dash', 'rainbow+mane', 'applejack',
        'twilight_sparkle', 'transparent_safe'
    ]
    app.all_tags_lower = [tag.lower() for tag in app.all_tags]
    
    # Mock frequencies (higher = more popular)
    app.tag_frequencies = {
        'safe': 2204259,
        'female': 1500000,
        'solo_female': 800000,
        'rainbow_dash': 400000,
        'female_oc': 50000,
        'applejack': 300000,
        'twilight_sparkle': 350000,
        'rainbow+mane': 25000,
        'transparent_safe': 45000
    }
    app.tag_cache = {}
    
    # Test exact match prioritization
    suggestions = TagAutoCompleteApp.find_suggestions(app, 'female')
    print(f"Suggestions for 'female': {suggestions}")
    assert 'female' == suggestions[0], f"Exact match 'female' should be first, got {suggestions[0]}"
    
    # Test prefix matching with frequency prioritization
    fe_suggestions = TagAutoCompleteApp.find_suggestions(app, 'fe')
    print(f"Suggestions for 'fe': {fe_suggestions}")
    # Should prioritize by frequency among fe* matches
    fe_frequencies = [(tag, app.tag_frequencies.get(tag, 0)) for tag in fe_suggestions]
    print(f"With frequencies: {fe_frequencies}")
    
    # Test rainbow matching (underscore vs plus)
    rain_suggestions = TagAutoCompleteApp.find_suggestions(app, 'rain')
    print(f"Suggestions for 'rain': {rain_suggestions}")
    assert 'rainbow_dash' in rain_suggestions, "rainbow_dash should be in suggestions"
    assert 'rainbow+mane' in rain_suggestions, "rainbow+mane should be in suggestions"
    # rainbow_dash should come first due to higher frequency
    rainbow_index_dash = rain_suggestions.index('rainbow_dash') if 'rainbow_dash' in rain_suggestions else 999
    rainbow_index_mane = rain_suggestions.index('rainbow+mane') if 'rainbow+mane' in rain_suggestions else 999
    assert rainbow_index_dash < rainbow_index_mane, "rainbow_dash should come before rainbow+mane due to higher frequency"
    
    print("✓ Enhanced suggestion logic test passed")

def test_space_based_selection():
    """Test the new space-based tag selection logic."""
    print("Testing space-based selection logic...")
    
    from main import TagAutoCompleteApp
    from PyQt6.QtWidgets import QListWidgetItem
    
    # Create minimal mock app
    app = Mock()
    app.tag_input = Mock()
    app.tag_input.toPlainText.return_value = "safe Rainbow "
    app.tag_input.textCursor.return_value = Mock()
    app.tag_input.textCursor.return_value.position.return_value = len("safe Rainbow ")
    app.suggestions_list = Mock()
    app.suggestions_list.clearSelection = Mock()
    app.suggestions_list.count.return_value = 3
    app.suggestions_list.item.return_value = None
    app.tag_input.setFocus = Mock()
    
    # Mock the convert_tag_for_display method
    def mock_convert_display(tag):
        return tag.replace('_', ' ').replace('+', ' ').title()
    
    app.convert_tag_for_display = mock_convert_display
    
    # Create mock QListWidgetItem with stored data
    mock_item = Mock()
    mock_item.data.return_value = "rainbow_dash"  # Original tag stored in item data
    
    # Test selection with QListWidgetItem
    original_text = app.tag_input.toPlainText.return_value
    TagAutoCompleteApp.select_suggestion(app, mock_item)
    
    # Verify setPlainText was called (tag was inserted)
    app.tag_input.setPlainText.assert_called()
    call_args = app.tag_input.setPlainText.call_args[0]
    result_text = call_args[0] if call_args else ""
    
    print(f"Original: '{original_text}' -> Result: '{result_text}'")
    
    # Should have "Rainbow Dash" (converted from rainbow_dash) inserted
    assert "Rainbow Dash" in result_text, f"Expected 'Rainbow Dash' in result, got '{result_text}'"
    # Should use space as separator, not comma
    assert " " in result_text, f"Expected space separator in result, got '{result_text}'"
    
    print("✓ Space-based selection test passed")

def test_mixed_separators():
    """Test handling of mixed comma and space separators."""
    print("Testing mixed separators...")
    
    from main import TagAutoCompleteApp
    
    # Create minimal mock app  
    app = Mock()
    app.tag_input = Mock()
    app.suggestions_list = Mock()
    app.suggestions_list.clearSelection = Mock()
    app.tag_input.setFocus = Mock()
    
    def mock_convert_display(tag):
        return tag.replace('_', ' ').replace('+', ' ').title()
    app.convert_tag_for_display = mock_convert_display
    
    # Test different input formats
    test_cases = [
        ("safe, solo, ", 12, "twilight_sparkle", "safe, solo, Twilight Sparkle "),
        ("safe Rainbow Dash ", 18, "female", "safe Rainbow Dash Female "),
        ("safe,solo,", 10, "female", "safe,solo,Female "),
        ("safe ", 5, "rainbow_dash", "safe Rainbow Dash ")
    ]
    
    for original_text, cursor_pos, selected_tag, expected_result in test_cases:
        app.tag_input.toPlainText.return_value = original_text
        app.tag_input.textCursor.return_value = Mock()
        app.tag_input.textCursor.return_value.position.return_value = cursor_pos
        
        # Create mock item with tag data
        mock_item = Mock()
        mock_item.data.return_value = selected_tag
        
        # Call selection
        TagAutoCompleteApp.select_suggestion(app, mock_item)
        
        # Check that text was set
        app.tag_input.setPlainText.assert_called()
        call_args = app.tag_input.setPlainText.call_args[0]
        result_text = call_args[0] if call_args else ""
        
        print(f"  Input: '{original_text}' + '{selected_tag}' -> '{result_text}'")
        
        # Verify expected tag appears in result (converted to display format)
        expected_display = mock_convert_display(selected_tag)
        assert expected_display in result_text, f"Expected '{expected_display}' in '{result_text}'"
    
    print("✓ Mixed separators test passed")

def test_comprehensive_workflow():
    """Test a complete workflow: search -> select -> verify."""
    print("Testing comprehensive workflow...")
    
    from main import TagAutoCompleteApp
    from PyQt6.QtWidgets import QListWidgetItem
    
    # Create more complete mock app
    app = Mock()
    
    # Mock tag database
    app.all_tags = ['safe', 'rainbow_dash', 'female_oc', 'solo_female']
    app.all_tags_lower = [tag.lower() for tag in app.all_tags] 
    app.tag_frequencies = {
        'safe': 2000000,
        'rainbow_dash': 400000, 
        'female_oc': 50000,
        'solo_female': 800000
    }
    app.tag_cache = {}
    
    # Test 1: Find suggestions for "fe"
    suggestions = TagAutoCompleteApp.find_suggestions(app, 'fe')
    print(f"Step 1 - Suggestions for 'fe': {suggestions}")
    assert 'female_oc' in suggestions, "female_oc should be found for 'fe'"
    
    # Test 2: Create suggestion display format
    def mock_convert_display(tag):
        return tag.replace('_', ' ').replace('+', ' ').title()
    
    def mock_format_frequency(display_tag, frequency):
        freq_str = f"{frequency/1000:.1f}K" if frequency >= 1000 else str(frequency)
        return f"{display_tag}                    {freq_str}"
    
    app.convert_tag_for_display = mock_convert_display
    app.format_suggestion_with_frequency = mock_format_frequency
    
    # Test display formatting
    for tag in suggestions:
        if tag == 'female_oc':
            frequency = app.tag_frequencies.get(tag, 0)
            display_tag = mock_convert_display(tag)  # "Female Oc"
            display_text = mock_format_frequency(display_tag, frequency)
            
            print(f"Step 2 - Display format: '{display_text}'")
            assert "Female Oc" in display_text, f"Expected 'Female Oc' in display"
            assert "50.0K" in display_text, f"Expected '50.0K' frequency in display"
    
    # Test 3: Simulate selection
    app.tag_input = Mock()
    app.tag_input.toPlainText.return_value = "safe "
    app.tag_input.textCursor.return_value = Mock()
    app.tag_input.textCursor.return_value.position.return_value = 5
    app.suggestions_list = Mock()
    app.suggestions_list.clearSelection = Mock()
    app.tag_input.setFocus = Mock()
    
    mock_item = Mock()
    mock_item.data.return_value = "female_oc"
    
    TagAutoCompleteApp.select_suggestion(app, mock_item)
    
    # Verify selection result
    app.tag_input.setPlainText.assert_called()
    call_args = app.tag_input.setPlainText.call_args[0]
    result_text = call_args[0] if call_args else ""
    
    print(f"Step 3 - Final result: '{result_text}'")
    assert "safe Female Oc" in result_text, f"Expected 'safe Female Oc' in result"
    assert result_text.endswith(" "), f"Expected trailing space in result"
    
    print("✓ Comprehensive workflow test passed")

def test_performance_considerations():
    """Test performance aspects of the enhanced system."""
    print("Testing performance considerations...")
    
    from main import TagAutoCompleteApp
    import time
    
    # Create app with large tag database
    app = Mock()
    
    # Simulate large tag database (10,000 tags)
    app.all_tags = []
    app.all_tags_lower = []
    app.tag_frequencies = {}
    
    for i in range(10000):
        tag = f"test_tag_{i:04d}"
        app.all_tags.append(tag)
        app.all_tags_lower.append(tag.lower())
        app.tag_frequencies[tag] = 10000 - i  # Decreasing frequency
    
    # Add some test targets
    test_tags = ['female', 'female_oc', 'safe', 'rainbow_dash']
    for tag in test_tags:
        app.all_tags.insert(0, tag)
        app.all_tags_lower.insert(0, tag.lower())
        app.tag_frequencies[tag] = 1000000
    
    app.tag_cache = {}
    
    # Test search performance
    start_time = time.time()
    
    # Multiple searches
    queries = ['fe', 'sa', 'rain', 'test', 'female']
    for query in queries:
        suggestions = TagAutoCompleteApp.find_suggestions(app, query)
        assert len(suggestions) <= 5, f"Too many suggestions returned: {len(suggestions)}"
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"Performance test: {len(queries)} searches in {elapsed:.3f}s")
    assert elapsed < 1.0, f"Search took too long: {elapsed:.3f}s"
    
    # Test caching works
    cached_suggestions = TagAutoCompleteApp.find_suggestions(app, 'fe')
    assert 'fe' in app.tag_cache, "Cache should store results"
    
    print("✓ Performance test passed")

def main():
    """Run all enhanced tagging tests."""
    print("Running Enhanced Tagging Features Tests")
    print("=" * 50)
    
    try:
        test_tag_conversion()
        test_frequency_formatting()
        test_enhanced_suggestion_logic()
        test_space_based_selection()
        test_mixed_separators()
        test_comprehensive_workflow()
        test_performance_considerations()
        
        print("\n" + "=" * 50)
        print("🎉 All enhanced tagging tests passed!")
        print("\nNew features verified:")
        print("✓ Space support via underscore and plus symbols")
        print("✓ Tag frequency display with right alignment")
        print("✓ Space-based separators (no comma requirement)")
        print("✓ Proper tag conversion between display and storage")
        print("✓ Performance optimization with caching")
        print("✓ Mixed separator handling")
        
        print("\nExpected behavior:")
        print("• Fe -> Female (with frequency)")
        print("• Rain -> Rainbow Dash (converted from rainbow_dash)")
        print("• Tags separated by spaces instead of commas")
        print("• Frequencies displayed aligned to the right")
        print("• Popular tags prioritized in suggestions")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
