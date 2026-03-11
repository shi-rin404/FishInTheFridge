from .._style import set_tab


class _TabLogicMixin:

    def _show_create(self):
        self.main_stack.setCurrentIndex(1)
        set_tab(self.create_tab, self.edit_tab)

    def _show_edit(self):
        self.main_stack.setCurrentIndex(0)
        set_tab(self.edit_tab, self.create_tab)

    def _show_add(self):
        self.edit_stack.setCurrentIndex(0)
        self.entry_preset_combo.setVisible(True)
        set_tab(self.add_tab, self.delete_tab)

    def _show_delete(self):
        self.edit_stack.setCurrentIndex(1)
        self.entry_preset_combo.setVisible(False)
        set_tab(self.delete_tab, self.add_tab)
