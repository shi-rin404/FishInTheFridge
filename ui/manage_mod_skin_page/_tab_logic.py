from PySide6.QtWidgets import QMessageBox

from .._style import set_tab


class _TabLogicMixin:
    def _show_manage(self):
        set_tab(self.manage_tab, self.add_tab)
        self.stack.setCurrentIndex(0)
        self.type_combo.setVisible(False)
        self._is_edit_mode = False
        self.add_tab.setText("Edit" if self.editor_mode == "mod" else "Add")

    def _show_add(self):
        set_tab(self.add_tab, self.manage_tab)
        self.stack.setCurrentIndex(1)
        self.save_btn.setText("Save")
        self._set_add_mode(False)

    def _forward_to_edit_form(self):
        """Edit button in the list loads the selected entry into the Add form."""
        if self.editor_mode == "skin":
            from modding.path_dictionary import skin_dict as ms_dict
        elif self.editor_mode == "mod":
            from modding.path_dictionary import mod_dict as ms_dict

        selected_key = self.ms_combo.currentText()
        if not selected_key or selected_key not in ms_dict:
            QMessageBox.warning(self, "No Selection", f"Please select a {self.editor_mode} from the list first.")
            return

        entry_dict = ms_dict[selected_key]
        self._edit_paths = dict(entry_dict)

        self.skin_name_input.setText(selected_key)

        self.type_combo.blockSignals(True)
        self.type_combo.clear()
        for key in entry_dict:
            self.type_combo.addItem(key)
        self.type_combo.addItem("Add New Data")
        self.type_combo.blockSignals(False)

        if entry_dict:
            first_type, first_path = next(iter(entry_dict.items()))
            self._current_type = first_type
            self.type_combo.setCurrentIndex(0)
            self.skin_path_input.setText(first_path)

        set_tab(self.add_tab, self.manage_tab)
        self.stack.setCurrentIndex(1)
        self.save_btn.setText("Save")
        self._set_add_mode(True)

    def _delete_entry(self):
        import json, os, shutil

        selected_name = self.ms_combo.currentText()
        if not selected_name:
            return

        reply = QMessageBox.question(
            self, "Delete Entry",
            f"Are you sure you want to delete \"{selected_name}\"?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        from core.variable_manager import program_variables

        if self.editor_mode == "skin":
            from modding.path_dictionary import skin_dict as ms_dict
            list_path = program_variables.skin_list_path
        else:
            from modding.path_dictionary import mod_dict as ms_dict
            list_path = program_variables.mod_list_path

        ms_dict.pop(selected_name, None)

        with open(list_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.pop(selected_name, None)
        with open(list_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        if self.editor_mode == "mod":
            from database.user.user_variables import user_variables

            matching_path = None
            for dirpath, _, filenames in os.walk(user_variables.mod_dir):
                for filename in filenames:
                    if filename == "mod.json":
                        filepath = os.path.join(dirpath, filename)
                        with open(filepath, "r", encoding="utf-8") as f:
                            mod_data = json.load(f)
                        if mod_data.get("name") == selected_name:
                            matching_path = filepath
                            break
                if matching_path:
                    break

            if matching_path:
                shutil.rmtree(os.path.dirname(matching_path))

        from core.automatic_processes.update_comboboxes import update_comboboxes
        update_comboboxes(self.editor_mode)

        self.ms_combo.setCurrentIndex(-1)
        self.ms_combo.lineEdit().clear()

    def _set_add_mode(self, is_edit: bool):
        self._is_edit_mode = is_edit
        add_only = not is_edit
        self.backslash_check.setVisible(add_only)
        self.help_btn.setVisible(add_only)
        self.auto_detect_check.setVisible(add_only)
        self.pin_toggle.setVisible(add_only)
        self._quick_grab_col_widget.setVisible(add_only)
        self.type_combo.setVisible(is_edit)
        self.skin_name_input.setReadOnly(is_edit)
        self.add_tab.setText("Edit" if (is_edit or self.editor_mode == "mod") else "Add")
