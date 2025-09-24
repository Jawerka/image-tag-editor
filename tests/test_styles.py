#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for Qt6 styles system.

This script validates the styles package and demonstrates how to use
the new modular styling system. It can be run independently to verify
that all style components work correctly.

Usage:
    python test_styles.py
"""

import sys
from pathlib import Path

def test_style_imports():
    """Test that all style modules can be imported correctly."""
    print("Testing style imports...")
    
    try:
        # Test importing the main package
        import styles
        print("✓ Main styles package imported successfully")
        
        # Test importing individual modules
        from styles import style_variables
        from styles import main_app_styles  
        from styles import macro_system_styles
        print("✓ Individual style modules imported successfully")
        
        # Test importing specific components
        from styles import COLORS, FONTS, DIMENSIONS
        from styles import get_complete_main_stylesheet, get_complete_macro_stylesheet
        print("✓ Style components imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_style_variables():
    """Test that style variables are properly defined."""
    print("\nTesting style variables...")
    
    try:
        from styles import COLORS, FONTS, DIMENSIONS, ICONS
        
        # Test that required colors exist
        required_colors = [
            'bg_main', 'bg_input', 'bg_button', 'text_main', 
            'border_main', 'selection_bg', 'accent_purple'
        ]
        
        for color in required_colors:
            if color not in COLORS:
                print(f"✗ Missing required color: {color}")
                return False
            if not COLORS[color].startswith('#'):
                print(f"✗ Invalid color format for {color}: {COLORS[color]}")
                return False
        
        print(f"✓ All {len(required_colors)} required colors found and valid")
        
        # Test that required fonts exist
        required_fonts = ['main', 'button', 'monospace']
        for font in required_fonts:
            if font not in FONTS:
                print(f"✗ Missing required font: {font}")
                return False
            if 'family' not in FONTS[font] or 'size' not in FONTS[font]:
                print(f"✗ Invalid font definition for {font}")
                return False
        
        print(f"✓ All {len(required_fonts)} required fonts found and valid")
        
        # Test dimensions
        required_dimensions = [
            'radius_medium', 'padding_medium', 'button_height_medium',
            'border_width', 'spacing_medium'
        ]
        
        for dim in required_dimensions:
            if dim not in DIMENSIONS:
                print(f"✗ Missing required dimension: {dim}")
                return False
            if not DIMENSIONS[dim].endswith('px'):
                print(f"✗ Invalid dimension format for {dim}: {DIMENSIONS[dim]}")
                return False
        
        print(f"✓ All {len(required_dimensions)} required dimensions found and valid")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing style variables: {e}")
        return False

def test_stylesheet_generation():
    """Test that stylesheets can be generated without errors."""
    print("\nTesting stylesheet generation...")
    
    try:
        from styles import (
            get_complete_main_stylesheet,
            get_complete_macro_stylesheet,
            get_unified_stylesheet
        )
        
        # Test main app stylesheet
        main_stylesheet = get_complete_main_stylesheet()
        if len(main_stylesheet) < 100:
            print("✗ Main stylesheet is too short")
            return False
        if 'QMainWindow' not in main_stylesheet:
            print("✗ Main stylesheet missing QMainWindow styles")
            return False
        print("✓ Main app stylesheet generated successfully")
        
        # Test macro system stylesheet
        macro_stylesheet = get_complete_macro_stylesheet()
        if len(macro_stylesheet) < 100:
            print("✗ Macro stylesheet is too short")
            return False
        if 'QDialog' not in macro_stylesheet:
            print("✗ Macro stylesheet missing QDialog styles")
            return False
        print("✓ Macro system stylesheet generated successfully")
        
        # Test unified stylesheet
        unified_stylesheet = get_unified_stylesheet()
        if len(unified_stylesheet) < 200:
            print("✗ Unified stylesheet is too short")
            return False
        print("✓ Unified stylesheet generated successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Error generating stylesheets: {e}")
        return False

def test_variable_substitution():
    """Test that variable substitution works correctly."""
    print("\nTesting variable substitution...")
    
    try:
        from styles.style_variables import apply_variables_to_stylesheet, get_stylesheet_variables
        
        # Test template with variables
        template = "background-color: {color_bg_main}; color: {color_text_main}; padding: {dim_padding_medium};"
        
        # Apply variables
        result = apply_variables_to_stylesheet(template)
        
        # Check that variables were replaced
        if '{' in result or '}' in result:
            print("✗ Variable substitution incomplete")
            print(f"Result: {result}")
            return False
        
        # Check that actual values are present
        from styles import COLORS, DIMENSIONS
        if COLORS['bg_main'] not in result:
            print(f"✗ Background color not substituted correctly")
            return False
        
        if DIMENSIONS['padding_medium'] not in result:
            print(f"✗ Padding dimension not substituted correctly")
            return False
        
        print("✓ Variable substitution working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Error testing variable substitution: {e}")
        return False

def test_theme_functions():
    """Test theme application functions."""
    print("\nTesting theme functions...")
    
    try:
        from styles import (
            apply_main_theme, apply_macro_theme, apply_unified_theme,
            switch_theme, validate_styles
        )
        
        # Test validation function
        validation_results = validate_styles()
        
        if not validation_results['style_variables']:
            print("✗ Style variables validation failed")
            return False
        
        if not validation_results['main_app_styles']:
            print("✗ Main app styles validation failed")  
            return False
        
        if not validation_results['macro_system_styles']:
            print("✗ Macro system styles validation failed")
            return False
        
        if validation_results['errors']:
            print(f"✗ Validation errors: {validation_results['errors']}")
            return False
        
        print("✓ All theme functions available and validation passed")
        return True
        
    except Exception as e:
        print(f"✗ Error testing theme functions: {e}")
        return False

def test_legacy_compatibility():
    """Test that legacy style functions work."""
    print("\nTesting legacy compatibility...")
    
    try:
        from styles import get_legacy_app_stylesheet, get_legacy_macro_stylesheet
        
        # Test legacy main app stylesheet
        legacy_main = get_legacy_app_stylesheet()
        if len(legacy_main) < 50:
            print("✗ Legacy main stylesheet too short")
            return False
        
        # Test legacy macro stylesheet  
        legacy_macro = get_legacy_macro_stylesheet()
        if len(legacy_macro) < 50:
            print("✗ Legacy macro stylesheet too short")
            return False
        
        print("✓ Legacy compatibility functions working")
        return True
        
    except Exception as e:
        print(f"✗ Error testing legacy compatibility: {e}")
        return False

def test_with_qt_application():
    """Test that styles can be applied to a real Qt application."""
    print("\nTesting with Qt application...")
    
    try:
        # Try to import PyQt6
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import Qt
        except ImportError:
            print("⚠ PyQt6 not available, skipping Qt application test")
            return True
        
        # Create a minimal application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test applying themes
        from styles import apply_unified_theme, get_unified_stylesheet
        
        # Apply unified theme
        apply_unified_theme(app)
        print("✓ Unified theme applied to Qt application")
        
        # Test that stylesheet was actually set
        current_stylesheet = app.styleSheet()
        if len(current_stylesheet) < 100:
            print("✗ Stylesheet not properly applied to application")
            return False
        
        print("✓ Qt application styling test passed")
        return True
        
    except Exception as e:
        print(f"✗ Error testing with Qt application: {e}")
        return False

def export_test_theme():
    """Export a test theme to verify file output."""
    print("\nExporting test theme...")
    
    try:
        from styles import export_theme_to_file
        
        test_file = "test_theme_export.css"
        export_theme_to_file(test_file, 'dark')
        
        # Check that file was created
        test_path = Path(test_file)
        if not test_path.exists():
            print(f"✗ Theme export file not created: {test_file}")
            return False
        
        # Check file content
        content = test_path.read_text(encoding='utf-8')
        if len(content) < 200:
            print("✗ Exported theme file too short")
            return False
        
        if 'QMainWindow' not in content or 'QDialog' not in content:
            print("✗ Exported theme missing expected content")
            return False
        
        # Clean up test file
        test_path.unlink()
        
        print("✓ Theme export test passed")
        return True
        
    except Exception as e:
        print(f"✗ Error exporting test theme: {e}")
        return False

def run_all_tests():
    """Run all style system tests."""
    print("=" * 60)
    print("TESTING QT6 STYLES SYSTEM")
    print("=" * 60)
    
    tests = [
        ("Style Imports", test_style_imports),
        ("Style Variables", test_style_variables),
        ("Stylesheet Generation", test_stylesheet_generation),
        ("Variable Substitution", test_variable_substitution),
        ("Theme Functions", test_theme_functions),
        ("Legacy Compatibility", test_legacy_compatibility),
        ("Qt Application", test_with_qt_application),
        ("Theme Export", export_test_theme),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test '{test_name}' crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed! The styles system is working correctly.")
        return True
    else:
        print(f"❌ {failed} test(s) failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
