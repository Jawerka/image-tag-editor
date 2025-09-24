#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test для проблемы с некорректной загрузкой тегов после отказа от сохранения изменений."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtTest import QTest

# Import the modules we're testing
from macro_system import MacroManager, MacroManagerDialog, Macro

def test_unsaved_decline_bug():
    """
    Тестируем сценарий:
    1. Загружаем макрос A
    2. Вносим изменения в теги
    3. Переключаемся на макрос B
    4. Отказываемся от сохранения (No)
    5. Проверяем, что макрос B загрузился корректно (не с тегами от макроса A)
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create temporary test manager
    temp_dir = Path(tempfile.mkdtemp())
    test_db_file = temp_dir / "test_macros.json"
    
    manager = MacroManager()
    manager.db_file = test_db_file
    manager.macros.clear()
    
    # Add test macros with distinct content
    macro_a = Macro("MacroA", "tag_a1, tag_a2, tag_a3", "Description A")
    macro_b = Macro("MacroB", "tag_b1, tag_b2, tag_b3", "Description B")
    
    manager.macros["MacroA"] = macro_a
    manager.macros["MacroB"] = macro_b
    
    # Create dialog
    dialog = MacroManagerDialog(manager)
    
    try:
        print("🧪 Testing unsaved decline bug...")
        
        # Step 1: Load Macro A
        dialog.macro_list.setCurrentRow(0)  # Assuming MacroA is first
        QTest.qWait(100)
        
        print(f"Step 1 - Loaded macro: {dialog.current_macro}")
        print(f"Original tags: {dialog.tags_editor.toPlainText()}")
        
        # Verify MacroA is loaded correctly
        assert dialog.current_macro == "MacroA"
        assert dialog.tags_editor.toPlainText() == "tag_a1, tag_a2, tag_a3"
        
        # Step 2: Make changes to tags
        modified_tags = "tag_a1, tag_a2, tag_a3, MODIFIED_TAG"
        dialog.tags_editor.setPlainText(modified_tags)
        QTest.qWait(100)
        
        print(f"Step 2 - Modified tags: {dialog.tags_editor.toPlainText()}")
        
        # Verify changes are detected
        has_changes = dialog._has_actual_changes()
        print(f"Has changes detected: {has_changes}")
        assert has_changes == True
        
        # Step 3: Try to switch to Macro B
        print("Step 3 - Switching to MacroB...")
        
        # Mock the ask_save_changes to return "No" (don't save)
        with patch.object(dialog, '_ask_save_changes') as mock_ask:
            mock_ask.return_value = QMessageBox.StandardButton.No
            
            # Switch to MacroB (should trigger unsaved changes prompt)
            dialog.macro_list.setCurrentRow(1)  # Assuming MacroB is second
            QTest.qWait(100)
            
            # Verify the prompt was called
            assert mock_ask.called, "Expected unsaved changes prompt"
            print("✅ Unsaved changes prompt was shown")
        
        # Step 4: Verify MacroB is loaded correctly (this is the bug test)
        print(f"Step 4 - After switch, current macro: {dialog.current_macro}")
        print(f"Tags after switch: {dialog.tags_editor.toPlainText()}")
        print(f"Description after switch: {dialog.description_input.text()}")
        
        # BUG CHECK: MacroB should be loaded with its original tags, not the modified tags from MacroA
        expected_tags = "tag_b1, tag_b2, tag_b3"
        actual_tags = dialog.tags_editor.toPlainText()
        
        if actual_tags == expected_tags:
            print("✅ PASS: MacroB loaded correctly with its own tags")
            return True
        elif actual_tags == modified_tags:
            print("❌ BUG FOUND: MacroB loaded with modified tags from MacroA!")
            print(f"   Expected: '{expected_tags}'")
            print(f"   Actual:   '{actual_tags}'")
            return False
        else:
            print(f"❓ UNEXPECTED: Got unexpected tags: '{actual_tags}'")
            return False
            
    finally:
        dialog.close()
        # Cleanup
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def main():
    """Main test runner."""
    print("🔍 Testing unsaved decline bug scenario...")
    
    try:
        success = test_unsaved_decline_bug()
        
        if success:
            print("\n🎉 Test passed! No bug found.")
            return 0
        else:
            print("\n⚠️  Bug confirmed! Need to fix the macro loading logic.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
