import re
from typing import Literal

from PySide6.QtWidgets import QMessageBox


class _SaveMixin:
    def save_for_skin(self) -> bool:
        from file_io.output.edit_json import merge_dict_json
        from core.variable_manager import program_variables

        if self._is_edit_mode:
            skin_path = self.skin_path_input.text()
            data_type = self.type_combo.currentText()
            if data_type == "Add New Data":
                self._handle_add_new_data_type()
                data_type = self.type_combo.currentText()
                if data_type == "Add New Data":
                    return False
            if not data_type:
                return False
        else:
            skin_path = self.skin_path_input.text().replace("/", "\\") if self.backslash_check.isChecked() else self.skin_path_input.text().replace("\\", "/")
            if self.auto_detect_check.isChecked():
                data_type = self.path_type_detector(skin_path)
                if data_type == "other":
                    QMessageBox.warning(
                        self, "Auto Detect Failed",
                        "Could not determine the data type from the path.\nPlease select the type manually."
                    )
                    self.auto_detect_check.setChecked(False)
                    return False
            else:
                from ._select_data_type_dialog import SelectDataTypeDialog
                preferred_type = getattr(self, "_preferred_data_type", "")
                dlg = SelectDataTypeDialog(parent=self, initial_type=preferred_type)
                if dlg.exec() != SelectDataTypeDialog.DialogCode.Accepted:
                    return False
                data_type = dlg.result_type
                self._preferred_data_type = None

        skin_name = self.skin_name_input.text()

        from modding.path_dictionary import skin_dict as ms_dict
        if skin_name in ms_dict and data_type in ms_dict[skin_name]:
            from ._duplicate_dialog import DuplicateDialog
            dlg = DuplicateDialog(skin_name, data_type, parent=self)
            if dlg.exec() != DuplicateDialog.DialogCode.Accepted:
                return False
            skin_name = dlg.new_name
            data_type = dlg.new_dtype

        if skin_name in ms_dict:
            merge_dict_json(
                program_variables.skin_list_path,
                skin_name,
                {data_type: skin_path}
            )
        else:
            from file_io.output.edit_json import edit_json
            edit_json(
                program_variables.skin_list_path,
                skin_name,
                {data_type: skin_path}
            )


        from core.automatic_processes.update_comboboxes import update_comboboxes
        update_comboboxes("skin")

        if self._is_edit_mode:
            self._edit_paths[data_type] = skin_path
        else:
            if not self.pin_toggle.isChecked():
                self.skin_name_input.setText("")
            self.skin_path_input.setText("")
            self.backslash_check.setChecked(False)
        return True

    def save_for_mod(self):
        pass

    def save_btn_dispatcher(self):
        try:
            if self.editor_mode == "skin":
                saved = self.save_for_skin()
            elif self.editor_mode == "mod":
                saved = self.save_for_mod()
            else:
                saved = False
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Could not save the {self.editor_mode} entry.\n\n{type(exc).__name__}: {exc}",
            )
            return

        if saved:
            QMessageBox.information(
                self,
                "Save Successful",
                f"{self.editor_mode.capitalize()} entry saved successfully.",
            )
        elif saved is False:
            QMessageBox.warning(
                self,
                "Save Failed",
                f"The {self.editor_mode} entry was not saved.",
            )

    def path_type_detector(self, path: str) -> Literal["skin", "item", "accessory", "other"]:
        if (("player" in path) or ("boss" in path)) and re.search(r"\w+_[cde]_[^_]+\.gim$", path):
            return "skin"
        elif "prop" in path:
            return "item"
        elif "guajian" in path:
            return "accessory"
        else:
            return "other"
