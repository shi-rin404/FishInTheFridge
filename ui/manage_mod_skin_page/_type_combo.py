from PySide6.QtWidgets import QInputDialog


class _TypeComboMixin:
    def _on_type_combo_changed(self, text: str):
        if text == "Add New Data":
            self._handle_add_new_data_type()
            return

        if self._is_edit_mode:
            if self._current_type is not None:
                self._edit_paths[self._current_type] = self.skin_path_input.text()
            self.skin_path_input.setText(self._edit_paths.get(text, ""))

        self._current_type = text

    def _handle_add_new_data_type(self):
        name, ok = QInputDialog.getText(self, "New Data Type", "Enter data type name:")
        if not ok or not name.strip():
            if self._current_type:
                self.type_combo.blockSignals(True)
                idx = self.type_combo.findText(self._current_type)
                if idx >= 0:
                    self.type_combo.setCurrentIndex(idx)
                self.type_combo.blockSignals(False)
            return

        new_type = name.strip().lower()
        insert_idx = self.type_combo.count() - 1  # insert before "Add New Data"

        self.type_combo.blockSignals(True)
        self.type_combo.insertItem(insert_idx, new_type)
        self.type_combo.setCurrentIndex(insert_idx)
        self.type_combo.blockSignals(False)

        if self._is_edit_mode:
            if self._current_type is not None:
                self._edit_paths[self._current_type] = self.skin_path_input.text()
            self._edit_paths[new_type] = ""
            self.skin_path_input.setText("")

        self._current_type = new_type
