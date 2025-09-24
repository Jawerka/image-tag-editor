#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive test suite for macro_system.py functionality.

This test suite covers:
1. Import priority - imported macros should overwrite existing ones
2. Unsaved changes handling in all scenarios
3. JSON file operations
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

# Import the modules we're testing
from macro_system import MacroManager, MacroManagerDialog, Macro

class TestMacroSystem:
    """Test class for macro system functionality."""
    
    def __init__(self):
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        # Create temporary directory for test files
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_db_file = self.temp_dir / "test_macros.json"
        
        print(f"Test temporary directory: {self.temp_dir}")
        
    def setup_test_manager(self) -> MacroManager:
        """Create a test macro manager with temporary database."""
        manager = MacroManager()
        manager.db_file = self.test_db_file
        manager.macros.clear()  # Start with empty macros
        return manager
        
    def create_test_macros_file(self, macros_data: Dict[str, Any]) -> Path:
        """Create a test macros JSON file with given data."""
        test_file = self.temp_dir / "import_test.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(macros_data, f, indent=2, ensure_ascii=False)
        return test_file
    
    def test_import_priority_overwrite(self):
        """Test that imported macros overwrite existing ones (import priority)."""
        print("\n=== Testing Import Priority (Overwrite Existing) ===")
        
        manager = self.setup_test_manager()
        
        # Create existing macro in database
        existing_macro = Macro(
            name="TestMacro",
            tags="old, tags, existing",
            description="Original description"
        )
        manager.macros["TestMacro"] = existing_macro
        
        print(f"Original macro: {existing_macro.tags}")
        print(f"Original description: {existing_macro.description}")
        
        # Create import file with same-named macro but different content
        import_data = {
            "version": "1.0",
            "macros": [
                {
                    "name": "TestMacro",
                    "tags": "new, imported, tags, priority",
                    "description": "Imported description should overwrite",
                    "created_date": "2024-01-01T10:00:00",
                    "last_used": "",
                    "use_count": 5,
                    "hotkey": "",
                    "category": "Imported"
                }
            ]
        }
        
        import_file = self.create_test_macros_file(import_data)
        
        # Import macros
        result = manager.import_macros(import_file)
        
        # Check results
        imported_macro = manager.get_macro("TestMacro")
        
        print(f"Import result: {result}")
        print(f"After import tags: {imported_macro.tags}")
        print(f"After import description: {imported_macro.description}")
        print(f"After import use_count: {imported_macro.use_count}")
        
        # CURRENT ISSUE: Import will fail because the logic only imports if name not in macros
        # This is the bug we need to fix
        if imported_macro.tags == "old, tags, existing":
            print("❌ ISSUE FOUND: Import did not overwrite existing macro")
            print("   Current logic: only imports if name not in existing macros")
            print("   Required: import should overwrite existing macros")
            return False
        elif imported_macro.tags == "new, imported, tags, priority":
            print("✅ Import priority working correctly")
            return True
        else:
            print(f"❓ Unexpected state: {imported_macro.tags}")
            return False
    
    def test_unsaved_changes_scenarios(self):
        """Test all unsaved changes scenarios as specified in requirements."""
        print("\n=== Testing Unsaved Changes Scenarios ===")
        
        manager = self.setup_test_manager()
        
        # Add test macros
        test_macros = [
            Macro("Macro1", "tag1, tag2", "Description 1"),
            Macro("Macro2", "tag3, tag4", "Description 2"),
            Macro("Macro3", "tag5, tag6", "Description 3")
        ]
        
        for macro in test_macros:
            manager.macros[macro.name] = macro
        
        dialog = MacroManagerDialog(manager)
        
        # Test scenarios
        scenario_results = []
        
        try:
            # Scenario 1: No changes made - switch macro - no warnings
            print("\n--- Scenario 1: No changes, switch macro ---")
            result1 = self._test_scenario_no_changes_switch(dialog)
            scenario_results.append(("No changes switch", result1))
            
            # Scenario 2: Changes made, saved, then switch - no warnings  
            print("\n--- Scenario 2: Changes made, saved, then switch ---")
            result2 = self._test_scenario_changes_saved_switch(dialog)
            scenario_results.append(("Changes saved switch", result2))
            
            # Scenario 3: Changes made, not saved, then switch - should warn
            print("\n--- Scenario 3: Changes made, not saved, then switch ---")
            result3 = self._test_scenario_changes_unsaved_switch(dialog)
            scenario_results.append(("Changes unsaved switch", result3))
            
            # Scenario 4: No changes made - close window - no warnings
            print("\n--- Scenario 4: No changes, close window ---")
            result4 = self._test_scenario_no_changes_close(dialog)
            scenario_results.append(("No changes close", result4))
            
            # Scenario 5: Changes made, saved, then close - no warnings
            print("\n--- Scenario 5: Changes made, saved, then close ---")
            result5 = self._test_scenario_changes_saved_close(dialog)
            scenario_results.append(("Changes saved close", result5))
            
            # Scenario 6: Changes made, not saved, then close - should warn
            print("\n--- Scenario 6: Changes made, not saved, then close ---")
            result6 = self._test_scenario_changes_unsaved_close(dialog)
            scenario_results.append(("Changes unsaved close", result6))
            
            # Scenario 7: Save button should not trigger unsaved changes prompts
            print("\n--- Scenario 7: Save button does not trigger unsaved changes prompts ---")
            result7 = self._test_scenario_save_button_no_prompts(dialog)
            scenario_results.append(("Save button no prompts", result7))
            
        finally:
            dialog.close()
        
        # Print results summary
        print("\n=== Unsaved Changes Test Results ===")
        all_passed = True
        for scenario_name, passed in scenario_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {scenario_name}")
            if not passed:
                all_passed = False
        
        return all_passed
    
    def _test_scenario_no_changes_switch(self, dialog: MacroManagerDialog) -> bool:
        """Test: No changes made, switch macro, should not warn."""
        # Select first macro
        dialog.macro_list.setCurrentRow(0)
        QTest.qWait(100)  # Allow UI to update
        
        # Verify it loaded
        if not dialog.current_macro:
            print("❌ Failed to load first macro")
            return False
            
        original_name = dialog.name_input.text()
        print(f"Loaded macro: {original_name}")
        
        # Don't make any changes
        
        # Check that no unsaved changes are detected
        has_changes = dialog._has_actual_changes()
        print(f"Has changes (should be False): {has_changes}")
        
        if has_changes:
            print("❌ False positive: detected changes when none were made")
            return False
        
        # Switch to second macro - should not prompt
        with patch.object(dialog, '_ask_save_changes') as mock_ask:
            dialog.macro_list.setCurrentRow(1)
            QTest.qWait(100)
            
            if mock_ask.called:
                print("❌ Unexpected prompt when no changes were made")
                return False
        
        print("✅ No prompt when switching without changes")
        return True
    
    def _test_scenario_changes_saved_switch(self, dialog: MacroManagerDialog) -> bool:
        """Test: Changes made, saved, then switch macro, should not warn."""
        # Select first macro
        dialog.macro_list.setCurrentRow(0)
        QTest.qWait(100)
        
        if not dialog.current_macro:
            print("❌ Failed to load first macro")
            return False
        
        original_tags = dialog.tags_editor.toPlainText()
        print(f"Original tags: {original_tags}")
        
        # Make changes
        new_tags = original_tags + ", new_tag"
        dialog.tags_editor.setPlainText(new_tags)
        QTest.qWait(100)
        
        # Verify changes are detected
        has_changes = dialog._has_actual_changes()
        print(f"Has changes after modification (should be True): {has_changes}")
        
        if not has_changes:
            print("❌ Changes not detected")
            return False
        
        # Save the changes
        dialog._save_macro()
        QTest.qWait(100)
        
        # Verify no unsaved changes after save
        has_changes_after_save = dialog._has_actual_changes()
        print(f"Has changes after save (should be False): {has_changes_after_save}")
        
        if has_changes_after_save:
            print("❌ Still shows unsaved changes after save")
            return False
        
        # Switch to second macro - should not prompt
        with patch.object(dialog, '_ask_save_changes') as mock_ask:
            dialog.macro_list.setCurrentRow(1)
            QTest.qWait(100)
            
            if mock_ask.called:
                print("❌ Unexpected prompt after saving changes")
                return False
        
        print("✅ No prompt when switching after saving changes")
        return True
    
    def _test_scenario_changes_unsaved_switch(self, dialog: MacroManagerDialog) -> bool:
        """Test: Changes made, not saved, then switch macro, should warn."""
        # Select first macro
        dialog.macro_list.setCurrentRow(0)
        QTest.qWait(100)
        
        if not dialog.current_macro:
            print("❌ Failed to load first macro")
            return False
        
        original_tags = dialog.tags_editor.toPlainText()
        print(f"Original tags: {original_tags}")
        
        # Make changes
        new_tags = original_tags + ", unsaved_change"
        dialog.tags_editor.setPlainText(new_tags)
        QTest.qWait(100)
        
        # Verify changes are detected
        has_changes = dialog._has_actual_changes()
        print(f"Has changes after modification (should be True): {has_changes}")
        
        if not has_changes:
            print("❌ Changes not detected")
            return False
        
        # DON'T save the changes
        
        # Try to switch to second macro - should prompt
        with patch.object(dialog, '_ask_save_changes') as mock_ask:
            mock_ask.return_value = QMessageBox.StandardButton.No  # Simulate "No" response
            
            dialog.macro_list.setCurrentRow(1)
            QTest.qWait(100)
            
            if not mock_ask.called:
                print("❌ Expected prompt for unsaved changes, but none occurred")
                return False
        
        print("✅ Correctly prompted for unsaved changes when switching")
        return True
    
    def _test_scenario_no_changes_close(self, dialog: MacroManagerDialog) -> bool:
        """Test: No changes made, close window, should not warn."""
        # Create fresh dialog
        manager = self.setup_test_manager()
        manager.macros["TestMacro"] = Macro("TestMacro", "tag1, tag2", "Description")
        
        test_dialog = MacroManagerDialog(manager)
        
        try:
            # Select macro
            test_dialog.macro_list.setCurrentRow(0)
            QTest.qWait(100)
            
            # Don't make changes
            
            # Check no changes detected
            has_changes = test_dialog._has_actual_changes()
            print(f"Has changes (should be False): {has_changes}")
            
            if has_changes:
                print("❌ False positive: detected changes when none were made")
                return False
            
            # Try to close - should not prompt
            with patch.object(test_dialog, '_ask_save_changes') as mock_ask:
                # Simulate close event
                from PyQt6.QtGui import QCloseEvent
                close_event = QCloseEvent()
                test_dialog.closeEvent(close_event)
                
                if mock_ask.called:
                    print("❌ Unexpected prompt when closing without changes")
                    return False
                    
                if close_event.isAccepted() == False:
                    print("❌ Close event was ignored when it should be accepted")
                    return False
            
            print("✅ No prompt when closing without changes")
            return True
            
        finally:
            test_dialog.close()
    
    def _test_scenario_changes_saved_close(self, dialog: MacroManagerDialog) -> bool:
        """Test: Changes made, saved, then close window, should not warn."""
        # Create fresh dialog
        manager = self.setup_test_manager()
        manager.macros["TestMacro"] = Macro("TestMacro", "tag1, tag2", "Description")
        
        test_dialog = MacroManagerDialog(manager)
        
        try:
            # Select macro
            test_dialog.macro_list.setCurrentRow(0)
            QTest.qWait(100)
            
            # Make and save changes
            original_tags = test_dialog.tags_editor.toPlainText()
            test_dialog.tags_editor.setPlainText(original_tags + ", saved_change")
            QTest.qWait(100)
            
            # Save
            test_dialog._save_macro()
            QTest.qWait(100)
            
            # Verify no unsaved changes
            has_changes = test_dialog._has_actual_changes()
            print(f"Has changes after save (should be False): {has_changes}")
            
            if has_changes:
                print("❌ Still shows unsaved changes after save")
                return False
            
            # Try to close - should not prompt
            with patch.object(test_dialog, '_ask_save_changes') as mock_ask:
                from PyQt6.QtGui import QCloseEvent
                close_event = QCloseEvent()
                test_dialog.closeEvent(close_event)
                
                if mock_ask.called:
                    print("❌ Unexpected prompt when closing after saving")
                    return False
                    
                if close_event.isAccepted() == False:
                    print("❌ Close event was ignored when it should be accepted")
                    return False
            
            print("✅ No prompt when closing after saving changes")
            return True
            
        finally:
            test_dialog.close()
    
    def _test_scenario_changes_unsaved_close(self, dialog: MacroManagerDialog) -> bool:
        """Test: Changes made, not saved, then close window, should warn."""
        # Create fresh dialog
        manager = self.setup_test_manager()
        manager.macros["TestMacro"] = Macro("TestMacro", "tag1, tag2", "Description")
        
        test_dialog = MacroManagerDialog(manager)
        
        try:
            # Select macro
            test_dialog.macro_list.setCurrentRow(0)
            QTest.qWait(100)
            
            # Make changes but don't save
            original_tags = test_dialog.tags_editor.toPlainText()
            test_dialog.tags_editor.setPlainText(original_tags + ", unsaved_close_change")
            QTest.qWait(100)
            
            # Verify changes detected
            has_changes = test_dialog._has_actual_changes()
            print(f"Has changes after modification (should be True): {has_changes}")
            
            if not has_changes:
                print("❌ Changes not detected")
                return False
            
            # Try to close - should prompt
            with patch.object(test_dialog, '_ask_save_changes') as mock_ask:
                mock_ask.return_value = QMessageBox.StandardButton.No  # Simulate "No" response
                
                from PyQt6.QtGui import QCloseEvent
                close_event = QCloseEvent()
                test_dialog.closeEvent(close_event)
                
                if not mock_ask.called:
                    print("❌ Expected prompt for unsaved changes when closing, but none occurred")
                    return False
            
            print("✅ Correctly prompted for unsaved changes when closing")
            return True
            
        finally:
            test_dialog.close()
    
    def _test_scenario_save_button_no_prompts(self, dialog: MacroManagerDialog) -> bool:
        """Test: Save button should not trigger unsaved changes prompts."""
        # Create fresh dialog
        manager = self.setup_test_manager()
        manager.macros["TestMacro"] = Macro("TestMacro", "tag1, tag2", "Description")
        
        test_dialog = MacroManagerDialog(manager)
        
        try:
            # Select macro
            test_dialog.macro_list.setCurrentRow(0)
            QTest.qWait(100)
            
            # Make changes
            original_tags = test_dialog.tags_editor.toPlainText()
            test_dialog.tags_editor.setPlainText(original_tags + ", save_test_tag")
            QTest.qWait(100)
            
            # Verify changes detected
            has_changes = test_dialog._has_actual_changes()
            print(f"Has changes before save (should be True): {has_changes}")
            
            if not has_changes:
                print("❌ Changes not detected before save")
                return False
            
            # Click Save button - should NOT trigger unsaved changes prompt
            with patch.object(test_dialog, '_ask_save_changes') as mock_ask:
                test_dialog._save_macro()
                QTest.qWait(100)
                
                if mock_ask.called:
                    print("❌ Save button incorrectly triggered unsaved changes prompt")
                    return False
            
            # Verify changes are now saved
            has_changes_after_save = test_dialog._has_actual_changes()
            print(f"Has changes after save (should be False): {has_changes_after_save}")
            
            if has_changes_after_save:
                print("❌ Still shows unsaved changes after save")
                return False
            
            print("✅ Save button works without triggering unsaved changes prompts")
            return True
            
        finally:
            test_dialog.close()
    
    def test_save_error_scenarios(self):
        """Test save error scenarios and error handling."""
        print("\n=== Testing Save Error Scenarios ===")
        
        manager = self.setup_test_manager()
        
        # Add test macros including conflicting names
        test_macros = [
            Macro("ExistingMacro1", "tag1, tag2", "Description 1"),
            Macro("ExistingMacro2", "tag3, tag4", "Description 2"),
        ]
        
        for macro in test_macros:
            manager.macros[macro.name] = macro
        
        dialog = MacroManagerDialog(manager)
        
        scenario_results = []
        
        try:
            # Test 1: Empty name should show error
            print("\n--- Test 1: Empty name error ---")
            result1 = self._test_empty_name_error(dialog)
            scenario_results.append(("Empty name error", result1))
            
            # Test 2: Duplicate name should show error  
            print("\n--- Test 2: Duplicate name error ---")
            result2 = self._test_duplicate_name_error(dialog)
            scenario_results.append(("Duplicate name error", result2))
            
        finally:
            dialog.close()
        
        # Print results summary
        print("\n=== Save Error Test Results ===")
        all_passed = True
        for scenario_name, passed in scenario_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {scenario_name}")
            if not passed:
                all_passed = False
        
        return all_passed
    
    def _test_empty_name_error(self, dialog: MacroManagerDialog) -> bool:
        """Test: Empty macro name should show error and not save."""
        # Select first macro
        dialog.macro_list.setCurrentRow(0)
        QTest.qWait(100)
        
        if not dialog.current_macro:
            print("❌ Failed to load first macro")
            return False
        
        # Clear the name field
        dialog.name_input.clear()
        QTest.qWait(100)
        
        # Try to save - should show error message
        with patch.object(QMessageBox, 'warning') as mock_warning:
            dialog._save_macro()
            QTest.qWait(100)
            
            if not mock_warning.called:
                print("❌ Expected warning for empty name, but none occurred")
                return False
            
            # Check the warning message
            call_args = mock_warning.call_args
            if call_args:
                warning_text = call_args[0][2]  # Third argument is the message
                if "name cannot be empty" in warning_text.lower():
                    print("✅ Correct warning shown for empty name")
                    return True
                else:
                    print(f"❌ Unexpected warning message: {warning_text}")
                    return False
            else:
                print("❌ Warning called but no arguments found")
                return False
    
    def _test_duplicate_name_error(self, dialog: MacroManagerDialog) -> bool:
        """Test: Duplicate macro name should show error and not save."""
        # Select first macro
        dialog.macro_list.setCurrentRow(0)
        QTest.qWait(100)
        
        if not dialog.current_macro:
            print("❌ Failed to load first macro")
            return False
        
        original_name = dialog.name_input.text()
        print(f"Original macro name: {original_name}")
        
        # Try to rename to existing macro name
        existing_name = "ExistingMacro2"  # This should already exist
        dialog.name_input.setText(existing_name)
        QTest.qWait(100)
        
        # Try to save - should show error message
        with patch.object(QMessageBox, 'warning') as mock_warning:
            dialog._save_macro()
            QTest.qWait(100)
            
            if not mock_warning.called:
                print("❌ Expected warning for duplicate name, but none occurred")
                return False
            
            # Check the warning message
            call_args = mock_warning.call_args
            if call_args:
                warning_text = call_args[0][2]  # Third argument is the message
                if "already exist" in warning_text.lower() or "save failed" in warning_text.lower():
                    print("✅ Correct warning shown for duplicate name")
                    return True
                else:
                    print(f"❌ Unexpected warning message: {warning_text}")
                    return False
            else:
                print("❌ Warning called but no arguments found")
                return False
    
    def cleanup(self):
        """Clean up test resources."""
        try:
            shutil.rmtree(self.temp_dir)
            print(f"\nCleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up temp directory: {e}")
    
    def run_all_tests(self):
        """Run all tests and return overall result."""
        print("🧪 Starting Macro System Comprehensive Tests")
        print("=" * 60)
        
        try:
            # Test import priority
            import_test_passed = self.test_import_priority_overwrite()
            
            # Test unsaved changes scenarios
            unsaved_test_passed = self.test_unsaved_changes_scenarios()
            
            # Test save error scenarios
            save_error_test_passed = self.test_save_error_scenarios()
            
            # Overall results
            print("\n" + "=" * 60)
            print("📊 OVERALL TEST RESULTS")
            print("=" * 60)
            
            print(f"Import Priority Test: {'✅ PASS' if import_test_passed else '❌ FAIL'}")
            print(f"Unsaved Changes Test: {'✅ PASS' if unsaved_test_passed else '❌ FAIL'}")
            print(f"Save Error Test: {'✅ PASS' if save_error_test_passed else '❌ FAIL'}")
            
            overall_passed = import_test_passed and unsaved_test_passed and save_error_test_passed
            print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_passed else '❌ SOME TESTS FAILED'}")
            
            if not overall_passed:
                print("\n🔧 Issues found that need to be fixed:")
                if not import_test_passed:
                    print("   - Import priority: imported macros should overwrite existing ones")
                if not unsaved_test_passed:
                    print("   - Unsaved changes handling has issues")
                if not save_error_test_passed:
                    print("   - Save error handling has issues")
            
            return overall_passed
            
        finally:
            self.cleanup()


def main():
    """Main test runner."""
    test_suite = TestMacroSystem()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! The macro system is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
