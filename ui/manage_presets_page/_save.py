from PySide6.QtWidgets import QMessageBox as _QMB

from core.automatic_processes.update_comboboxes import update_comboboxes
from error_handler.ensure_exception import ensure_exception


class _SaveMixin:

    # ── Preset combo loaders ───────────────────────────────────────────────

    def _reload_preset_combos(self) -> None:
        """Reload entry_preset_combo and assoc_preset_combo from presets.json."""
        from modding.preset_manager import read_presets
        data = ensure_exception(read_presets, ()) or {}
        for combo in (self.entry_preset_combo, self.assoc_preset_combo):
            combo.clear()
            for name in data:
                combo.addItem(name)
            combo.setCurrentIndex(-1)

    def _reload_assoc_combos(self, preset_name: str) -> None:
        """Populate assoc_combo_combo with 'skin → mod' entries of the selected preset."""
        self.assoc_combo_combo.clear()
        if not preset_name:
            return
        from modding.preset_manager import read_preset_entries
        entries = ensure_exception(read_preset_entries, (preset_name,))
        if not entries:
            return
        for skin, mod in entries.items():
            self.assoc_combo_combo.addItem(f"{skin} \u2192 {mod}")
        self.assoc_combo_combo.setCurrentIndex(-1)

    # ── Button handlers ────────────────────────────────────────────────────

    def _on_create_preset(self) -> None:
        from modding.preset_manager import create_preset
        preset_name = self.preset_name_input.text().strip()
        if ensure_exception(create_preset, (preset_name,)):
            update_comboboxes("preset")
            self.preset_name_input.clear()
            _QMB.information(
                self, "Preset Created",
                f"Preset '{preset_name}' was created successfully.",
            )

    def _on_delete(self) -> None:
        preset_name = self.assoc_preset_combo.currentText()
        if self.delete_preset_check.isChecked():
            from modding.preset_manager import delete_preset
            if ensure_exception(delete_preset, (preset_name,)):
                update_comboboxes("preset")
                self.assoc_combo_combo.clear()
                _QMB.information(
                    self, "Preset Deleted",
                    f"Preset '{preset_name}' was deleted.",
                )
        else:
            combo_text = self.assoc_combo_combo.currentText()
            skin_name = combo_text.split(" \u2192 ")[0]
            from modding.preset_manager import delete_entry
            if ensure_exception(delete_entry, (preset_name, skin_name)):
                self._reload_assoc_combos(preset_name)
                _QMB.information(
                    self, "Entry Deleted",
                    f"'{combo_text}' was removed from preset '{preset_name}'.",
                )

    def _on_add_entry(self) -> None:
        from modding.preset_manager import add_entry
        preset_name = self.entry_preset_combo.currentText()
        skin_name = self.skin_combo.currentText()
        mod_name = self.mod_combo.currentText()
        if ensure_exception(add_entry, (preset_name, skin_name, mod_name)):
            self.skin_combo.setCurrentIndex(-1)
            self.mod_combo.setCurrentIndex(-1)
            _QMB.information(
                self, "Entry Added",
                f"'{skin_name} \u2192 {mod_name}' was added to preset '{preset_name}'.",
            )
