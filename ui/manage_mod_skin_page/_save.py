import re
from typing import Literal

from PySide6.QtWidgets import QMessageBox


class _SaveMixin:
    def save_for_skin(self):
        from file_io.output.edit_json import merge_dict_json
        from core.variable_manager import program_variables

        if self._is_edit_mode:
            skin_path = self.skin_path_input.text()
            data_type = self.type_combo.currentText()
            if data_type == "Add New Data":
                self._handle_add_new_data_type()
                data_type = self.type_combo.currentText()
                if data_type == "Add New Data":
                    return
            if not data_type:
                return
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
                    return
            else:
                from ._select_data_type_dialog import SelectDataTypeDialog
                dlg = SelectDataTypeDialog(parent=self)
                if dlg.exec() != SelectDataTypeDialog.DialogCode.Accepted:
                    return
                data_type = dlg.result_type

        skin_name = self.skin_name_input.text()

        from modding.path_dictionary import skin_dict as ms_dict
        if skin_name in ms_dict and data_type in ms_dict[skin_name]:
            from ._duplicate_dialog import DuplicateDialog
            dlg = DuplicateDialog(skin_name, data_type, parent=self)
            if dlg.exec() != DuplicateDialog.DialogCode.Accepted:
                return
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
                {skin_name: {data_type: skin_path}}
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

    def save_for_mod(self):
        pass

    def save_btn_dispatcher(self):
        if self.editor_mode == "skin":
            self.save_for_skin()
        elif self.editor_mode == "mod":
            self.save_for_mod()

    def path_type_detector(self, path: str) -> Literal["skin", "item", "accessory", "other"]:
        if (("player" in path) or ("boss" in path)) and re.search(r"\w+_[cde]_[^_]+\.gim$", path):
            return "skin"
        elif "prop" in path:
            return "item"
        elif "guajian" in path:
            return "accessory"
        else:
            return "other"
