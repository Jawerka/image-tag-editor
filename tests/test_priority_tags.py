#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for priority tags functionality.

This module tests the important tags reordering functionality.
"""

import sys
import unittest
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import TagAutoCompleteApp
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest


class TestPriorityTags(unittest.TestCase):
    """Test priority tags functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up each test."""
        self.window = TagAutoCompleteApp()
    
    def tearDown(self):
        """Clean up after each test."""
        self.window.close()
    
    def test_parse_tags_from_text_comma_separated(self):
        """Test parsing comma-separated tags."""
        text = "safe, oc:dyx, alicorn, pony, solo, artist:nekro-led"
        expected = ["safe", "oc:dyx", "alicorn", "pony", "solo", "artist:nekro-led"]
        result = self.window._parse_tags_from_text(text)
        self.assertEqual(result, expected)
    
    def test_parse_tags_from_text_space_separated(self):
        """Test parsing space-separated tags (now only comma is supported)."""
        text = "safe oc:dyx alicorn pony solo artist:nekro-led"
        # Since we only use comma as separator, this should be treated as one tag
        expected = ["safe oc:dyx alicorn pony solo artist:nekro-led"]
        result = self.window._parse_tags_from_text(text)
        self.assertEqual(result, expected)
    
    def test_parse_tags_from_text_empty(self):
        """Test parsing empty text."""
        result = self.window._parse_tags_from_text("")
        self.assertEqual(result, [])
    
    def test_parse_tags_from_text_with_duplicates(self):
        """Test parsing comma-separated tags with duplicates removal."""
        text = "safe, oc:dyx, SAFE, alicorn, pony, Safe, artist:nekro-led, OC:DYX"
        # Should remove duplicates (case-insensitive) but keep first occurrence
        expected = ["safe", "oc:dyx", "alicorn", "pony", "artist:nekro-led"]
        result = self.window._parse_tags_from_text(text)
        self.assertEqual(result, expected)
    
    def test_parse_tags_from_text_with_whitespace_duplicates(self):
        """Test parsing with whitespace and duplicate handling."""
        text = "  safe  ,  oc:dyx  , safe , alicorn ,  oc:dyx  "
        # Should trim whitespace and remove duplicates
        expected = ["safe", "oc:dyx", "alicorn"]
        result = self.window._parse_tags_from_text(text)
        self.assertEqual(result, expected)
    
    def test_is_species_tag_basic(self):
        """Test basic species tag detection."""
        self.assertTrue(self.window._is_species_tag("pony"))
        self.assertTrue(self.window._is_species_tag("alicorn"))
        self.assertTrue(self.window._is_species_tag("earth pony"))
        self.assertTrue(self.window._is_species_tag("unicorn"))
        self.assertTrue(self.window._is_species_tag("pegasus"))
        self.assertTrue(self.window._is_species_tag("dragon"))
        
        self.assertFalse(self.window._is_species_tag("safe"))
        self.assertFalse(self.window._is_species_tag("cute"))
        self.assertFalse(self.window._is_species_tag("solo"))
    
    def test_is_species_tag_with_underscores(self):
        """Test species tag detection with underscores."""
        self.assertTrue(self.window._is_species_tag("earth_pony"))
        self.assertTrue(self.window._is_species_tag("bat_pony"))
    
    def test_priority_patterns(self):
        """Test priority pattern recognition."""
        # Test artist tags
        self.assertTrue("artist:nekro-led".lower().startswith("artist:"))
        self.assertTrue("artist:test".lower().startswith("artist:"))
        self.assertFalse("safe".lower().startswith("artist:"))
        
        # Test OC tags
        self.assertTrue("oc:dyx".lower().startswith("oc:"))
        self.assertTrue("oc:test character".lower().startswith("oc:"))
        self.assertFalse("pony".lower().startswith("oc:"))
        
        # Test quantity tags
        quantity_tags = ['solo', 'duo', 'trio', 'group', 'crowd']
        for tag in quantity_tags:
            self.assertIn(tag.lower().strip(), quantity_tags)
        
        self.assertNotIn("pony", quantity_tags)
    
    def test_move_important_tags_basic(self):
        """Test basic tag reordering functionality."""
        # Set up test text
        test_text = "safe, clothes, collar, oc:dyx, alicorn, pony, solo, artist:nekro-led"
        self.window.tag_input.setPlainText(test_text)
        
        # Enable the button (simulate image loaded)
        self.window.priority_tags_button.setEnabled(True)
        
        # Call the function
        self.window.move_important_tags_to_top()
        
        # Get result
        result_text = self.window.tag_input.toPlainText()
        result_tags = [tag.strip() for tag in result_text.split(',') if tag.strip()]
        
        # Check that important tags are at the beginning
        important_tags = ["artist:nekro-led", "oc:dyx", "solo", "alicorn", "pony"]
        regular_tags = ["safe", "clothes", "collar"]
        
        # The result should have important tags first
        expected_order = important_tags + regular_tags
        
        # Check that all tags are present
        for tag in expected_order:
            self.assertIn(tag, result_tags)
        
        # Check that important tags come before regular tags
        artist_pos = result_tags.index("artist:nekro-led")
        oc_pos = result_tags.index("oc:dyx")
        solo_pos = result_tags.index("solo")
        safe_pos = result_tags.index("safe")
        
        # Important tags should come before regular tags
        self.assertLess(artist_pos, safe_pos)
        self.assertLess(oc_pos, safe_pos)
        self.assertLess(solo_pos, safe_pos)
    
    def test_move_important_tags_already_ordered(self):
        """Test when tags are already in optimal order."""
        # Set up text that's already properly ordered
        test_text = "artist:nekro-led, oc:dyx, solo, alicorn, pony, safe, clothes"
        self.window.tag_input.setPlainText(test_text)
        
        # Enable the button
        self.window.priority_tags_button.setEnabled(True)
        
        # Call the function
        self.window.move_important_tags_to_top()
        
        # Result should be the same
        result_text = self.window.tag_input.toPlainText()
        # Remove spaces for comparison
        original_normalized = test_text.replace(" ", "")
        result_normalized = result_text.replace(" ", "")
        
        # Should be essentially the same (allowing for formatting differences)
        original_tags = [tag.strip() for tag in test_text.split(',')]
        result_tags = [tag.strip() for tag in result_text.split(',')]
        self.assertEqual(original_tags, result_tags)
    
    def test_move_important_tags_empty_text(self):
        """Test with empty text."""
        self.window.tag_input.setPlainText("")
        self.window.priority_tags_button.setEnabled(True)
        
        # Should not crash
        self.window.move_important_tags_to_top()
        
        # Text should remain empty
        result_text = self.window.tag_input.toPlainText()
        self.assertEqual(result_text, "")
    
    def test_move_important_tags_single_tag(self):
        """Test with single tag."""
        self.window.tag_input.setPlainText("solo")
        self.window.priority_tags_button.setEnabled(True)
        
        # Should not crash
        self.window.move_important_tags_to_top()
        
        # Should remain the same
        result_text = self.window.tag_input.toPlainText()
        self.assertEqual(result_text.strip(), "solo")
    
    def test_button_enabled_state(self):
        """Test that button is properly enabled/disabled."""
        # Now button is always enabled (works without image too)
        self.assertTrue(self.window.priority_tags_button.isEnabled())
        
        # Should remain enabled when image is loaded (simulated)
        self.window.current_image_path = Path("test.jpg")
        self.assertTrue(self.window.priority_tags_button.isEnabled())
    
    def test_button_connection(self):
        """Test that button is properly connected."""
        # Check that the button has the signal connected
        self.assertTrue(self.window.priority_tags_button.receivers(
            self.window.priority_tags_button.clicked) > 0)


class TestPriorityTagsIntegration(unittest.TestCase):
    """Integration tests for priority tags with UI."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up each test."""
        self.window = TagAutoCompleteApp()
        self.window.show()
    
    def tearDown(self):
        """Clean up after each test."""
        self.window.close()
    
    def test_button_click_integration(self):
        """Test actual button click behavior."""
        # Set up test scenario
        test_text = "safe, cute, oc:rainbow dash, pegasus, solo, artist:test"
        self.window.tag_input.setPlainText(test_text)
        self.window.priority_tags_button.setEnabled(True)
        
        # Simulate button click
        QTest.mouseClick(self.window.priority_tags_button, Qt.MouseButton.LeftButton)
        
        # Process events
        self.app.processEvents()
        
        # Check result
        result_text = self.window.tag_input.toPlainText()
        result_tags = [tag.strip() for tag in result_text.split(',') if tag.strip()]
        
        # Verify that important tags moved to front
        artist_pos = next((i for i, tag in enumerate(result_tags) if tag.startswith("artist:")), -1)
        oc_pos = next((i for i, tag in enumerate(result_tags) if tag.startswith("oc:")), -1)
        solo_pos = next((i for i, tag in enumerate(result_tags) if tag == "solo"), -1)
        safe_pos = next((i for i, tag in enumerate(result_tags) if tag == "safe"), -1)
        
        # Important tags should come before regular tags
        self.assertNotEqual(artist_pos, -1)
        self.assertNotEqual(oc_pos, -1)
        self.assertNotEqual(solo_pos, -1)
        self.assertNotEqual(safe_pos, -1)
        
        self.assertLess(artist_pos, safe_pos)
        self.assertLess(oc_pos, safe_pos)
        self.assertLess(solo_pos, safe_pos)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
