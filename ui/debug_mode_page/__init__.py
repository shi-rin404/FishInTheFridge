from PySide6.QtWidgets import (
    QWidget, QApplication, QPushButton, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QProgressBar, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QFrame, QCheckBox, QDialog, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, QPoint, QRect, QTimer
from PySide6.QtGui import QCursor

from .._style import COMMON_STYLE, MUTED, set_tab
from .._widgets import WindowControls
from error_handler.ensure_exception import ensure_exception


_DISABLED_STYLE = f"QPushButton:disabled {{ color: {MUTED}; border-color: {MUTED}; }}"


class _DropdownPopup(QFrame):
    """Generic dropdown popup that tracks if it was closed by its toggle button."""

    def __init__(self, dropdown_btn: QPushButton):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Popup | Qt.FramelessWindowHint)
        self.setStyleSheet(COMMON_STYLE)
        self._dropdown_btn = dropdown_btn
        self.closed_by_dropdown = False

    def hideEvent(self, event):
        cursor_pos = QCursor.pos()
        tl = self._dropdown_btn.mapToGlobal(self._dropdown_btn.rect().topLeft())
        self.closed_by_dropdown = QRect(tl, self._dropdown_btn.size()).contains(cursor_pos)
        super().hideEvent(event)


class DebugModePage(QWidget):
    debug_mode_page = None

    def __init__(self, parent=None):
        DebugModePage.debug_mode_page = self
        super().__init__(parent=parent)
        self.setStyleSheet(COMMON_STYLE)
        self.resize(800, 420)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self._drag_pos = QPoint()
        self._read_handle = None
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(200)  # 5 Hz — change to 16 for 60 Hz
        self._refresh_timer.timeout.connect(self._refresh_values)
        self._build_ui()
        self._load_from_cache()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top Row ────────────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 5, 8, 0)
        top_row.setSpacing(12)
        top_row.addStretch()

        self.window_controls = WindowControls()
        self.window_controls.minimize_requested.connect(self.showMinimized)
        self.window_controls.close_requested.connect(self.close)
        top_row.addWidget(self.window_controls)
        root.addLayout(top_row)

        # ── Content ────────────────────────────────────────────
        content = QVBoxLayout()
        content.setContentsMargins(60, 16, 60, 50)
        content.setSpacing(16)

        title = QLabel("Debug Mode")
        title.setObjectName("title")
        content.addWidget(title)

        # ── Tab row + progress bar (same row) ──────────────────
        tab_row = QHBoxLayout()
        tab_row.setSpacing(0)

        self.change_tab = QPushButton("Change Values")
        self.manage_tab = QPushButton("Manage Values")

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        tab_row.addWidget(self.change_tab)
        tab_row.addWidget(self.manage_tab)
        tab_row.addStretch()
        tab_row.addWidget(self.progress_bar)
        content.addLayout(tab_row)

        # ── Stacked content ────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_change_panel())
        self.stack.addWidget(self._build_manage_panel())
        content.addWidget(self.stack)
        content.addStretch()

        self.change_tab.clicked.connect(self._show_change)
        self.manage_tab.clicked.connect(self._show_manage)
        self._show_change()

        root.addLayout(content)

    # ── Panels ─────────────────────────────────────────────────

    def _build_change_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.current_value_input = QLineEdit()
        self.current_value_input.setPlaceholderText("Current Value")

        self.change_as_input = QLineEdit()
        self.change_as_input.setPlaceholderText("Change as")

        apply_row = QHBoxLayout()
        apply_row.addStretch()
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setEnabled(False)
        self.apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_btn.setStyleSheet(_DISABLED_STYLE)
        apply_row.addWidget(self.apply_btn)

        layout.addWidget(self.current_value_input)
        layout.addWidget(self.change_as_input)
        layout.addLayout(apply_row)
        layout.addStretch()

        self.current_value_input.textChanged.connect(self._update_apply_btn)
        self.change_as_input.textChanged.connect(self._update_apply_btn)
        self.apply_btn.clicked.connect(self._on_apply)

        return panel

    def _build_manage_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.values_list = QListWidget()
        self.values_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.values_list)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.retrieve_btn = QPushButton("Retrieve")
        self.retrieve_btn.setObjectName("success")
        self.retrieve_btn.setEnabled(False)
        self.retrieve_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.retrieve_btn.setStyleSheet(_DISABLED_STYLE)
        action_row.addWidget(self.retrieve_btn)

        self.unfollow_btn = QPushButton("Unfollow")
        self.unfollow_btn.setObjectName("danger")
        self.unfollow_btn.setEnabled(False)
        self.unfollow_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.unfollow_btn.setStyleSheet(
            f"QPushButton#danger:disabled {{ color: {MUTED}; border-color: {MUTED}; }}"
        )
        action_row.addWidget(self.unfollow_btn)
        action_row.addStretch()

        # Split button: edit_values_btn | edit_values_dropdown_btn
        edit_split_widget = QWidget()
        edit_split = QHBoxLayout(edit_split_widget)
        edit_split.setSpacing(0)
        edit_split.setContentsMargins(0, 0, 0, 0)

        self.edit_values_btn = QPushButton("Edit")
        self.edit_values_btn.setEnabled(False)
        self.edit_values_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_values_btn.setStyleSheet(
            f"QPushButton {{ border-top-right-radius: 0; border-bottom-right-radius: 0; }}"
            f"QPushButton:hover {{ border-top-right-radius: 0; border-bottom-right-radius: 0; }}"
            f"QPushButton:disabled {{ color: {MUTED}; border-color: {MUTED}; border-top-right-radius: 0; border-bottom-right-radius: 0; }}"
        )

        self.edit_values_dropdown_btn = QPushButton("▾")
        self.edit_values_dropdown_btn.setFixedWidth(22)
        self.edit_values_dropdown_btn.setEnabled(False)
        self.edit_values_dropdown_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_values_dropdown_btn.setStyleSheet(
            f"QPushButton {{ border-top-left-radius: 0; border-bottom-left-radius: 0; border-left: none; padding: 8px 4px; }}"
            f"QPushButton:hover {{ border-top-left-radius: 0; border-bottom-left-radius: 0; }}"
            f"QPushButton:disabled {{ color: {MUTED}; border-color: {MUTED}; border-top-left-radius: 0; border-bottom-left-radius: 0; }}"
        )

        edit_split.addWidget(self.edit_values_btn)
        edit_split.addWidget(self.edit_values_dropdown_btn)
        action_row.addWidget(edit_split_widget)

        layout.addLayout(action_row)

        # Dropdown popup for edit_values_dropdown_btn
        self._edit_dropdown = _DropdownPopup(self.edit_values_dropdown_btn)
        _dropdown_layout = QVBoxLayout(self._edit_dropdown)
        _dropdown_layout.setContentsMargins(12, 8, 12, 8)
        self.dont_check_length = QCheckBox("Don't Check Value Length")
        self.dont_check_length.setStyleSheet(
            "QCheckBox { color: #CC2200; font-weight: bold; }"
        )
        _dropdown_layout.addWidget(self.dont_check_length)

        self.values_list.itemSelectionChanged.connect(self._update_action_btns)
        self.retrieve_btn.clicked.connect(self._on_retrieve)
        self.unfollow_btn.clicked.connect(self._on_unfollow)
        self.edit_values_btn.clicked.connect(self._on_edit_values)
        self.edit_values_dropdown_btn.clicked.connect(self._toggle_edit_dropdown)

        return panel

    # ── Tab switching ───────────────────────────────────────────

    def _show_change(self):
        set_tab(self.change_tab, self.manage_tab)
        self.stack.setCurrentIndex(0)
        self._stop_refresh()

    def _show_manage(self):
        set_tab(self.manage_tab, self.change_tab)
        self.stack.setCurrentIndex(1)
        self._start_refresh()

    def closeEvent(self, event):
        self._stop_refresh()
        super().closeEvent(event)

    # ── Button state guards ─────────────────────────────────────

    def _update_apply_btn(self):
        enabled = bool(self.current_value_input.text()) and bool(self.change_as_input.text())
        self.apply_btn.setEnabled(enabled)

    def _update_action_btns(self):
        enabled = len(self.values_list.selectedItems()) > 0
        self.retrieve_btn.setEnabled(enabled)
        self.unfollow_btn.setEnabled(enabled)
        self.edit_values_btn.setEnabled(enabled)
        self.edit_values_dropdown_btn.setEnabled(enabled)

    # ── Refresh ─────────────────────────────────────────────────

    def _start_refresh(self):
        if self.values_list.count() == 0:
            return
        if not self._read_handle:
            self._open_read_handle()
        if self._read_handle:
            self._refresh_timer.start()

    def _stop_refresh(self):
        self._refresh_timer.stop()
        self._close_read_handle()

    def _open_read_handle(self):
        try:
            import base64
            from modding.modder import _pid_by_name, _k32, PROCESS_VM_READ, PROCESS_QUERY_INFO
            proc = base64.decodebytes(b"ZHdyZy5leGU=").decode()
            pid = _pid_by_name(proc)
            handle = _k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFO, False, pid)
            if handle:
                self._read_handle = handle
        except Exception:
            pass  # game not running — timer stays stopped

    def _close_read_handle(self):
        if self._read_handle:
            from modding.modder import _k32
            _k32.CloseHandle(self._read_handle)
            self._read_handle = None

    def _refresh_values(self):
        import ctypes
        from modding.modder import _k32
        from modding.debug_actions import debug_cache

        bytes_read = ctypes.c_size_t(0)
        for i in range(self.values_list.count()):
            item = self.values_list.item(i)
            addr = item.data(Qt.ItemDataRole.UserRole)
            initial = debug_cache.get(addr, "")
            read_len = max(len(initial.encode("utf-8")) + 8, 64)
            buf = (ctypes.c_char * read_len)()
            ok = _k32.ReadProcessMemory(
                self._read_handle, ctypes.c_void_p(addr), buf, read_len, ctypes.byref(bytes_read)
            )
            if ok and bytes_read.value > 0:
                current = bytes(buf[:bytes_read.value]).decode("utf-8", errors="replace").split("\x00")[0]
                item.setText(f"0x{addr:016X}  {current}")
            else:
                # Process closed or address freed — stop polling
                self._stop_refresh()
                return

    # ── Values list ─────────────────────────────────────────────

    def _load_from_cache(self):
        from modding.debug_actions import debug_cache
        if debug_cache:
            self._populate_values_list(dict(debug_cache))

    def _populate_values_list(self, entries: dict[int, str]):
        self.values_list.clear()
        for addr, initial_value in entries.items():
            item = QListWidgetItem(f"0x{addr:016X}  {initial_value}")
            item.setData(Qt.ItemDataRole.UserRole, addr)
            self.values_list.addItem(item)
        self._update_action_btns()

    def _get_selected_addrs(self) -> list[int]:
        return [item.data(Qt.ItemDataRole.UserRole) for item in self.values_list.selectedItems()]

    # ── Dropdown toggle ─────────────────────────────────────────

    def _toggle_edit_dropdown(self):
        if self._edit_dropdown.closed_by_dropdown:
            self._edit_dropdown.closed_by_dropdown = False
            return
        tl = self.edit_values_dropdown_btn.mapToGlobal(
            self.edit_values_dropdown_btn.rect().bottomLeft()
        )
        self._edit_dropdown.adjustSize()
        self._edit_dropdown.move(tl.x(), tl.y() + 4)
        self._edit_dropdown.show()

    # ── Actions ─────────────────────────────────────────────────

    def _on_apply(self):
        from modding.debug_actions import debug_scan
        search = self.current_value_input.text().strip()
        change_to = self.change_as_input.text().strip()
        if not search or not change_to:
            return

        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)

        def progress_cb(scanned, total):
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(scanned)
            QApplication.processEvents()

        result = ensure_exception(debug_scan, (search, change_to, progress_cb))
        if result is not None:
            self.progress_bar.setValue(self.progress_bar.maximum())
            self._populate_values_list(result)

    def _on_retrieve(self):
        from modding.debug_actions import debug_retrieve
        addrs = self._get_selected_addrs()
        if not addrs:
            return
        check_length = not self.dont_check_length.isChecked()
        result = ensure_exception(debug_retrieve, (addrs, check_length))
        if result is not None:
            _, skipped = result
            if skipped and check_length:
                skipped_strs = "\n".join(f"0x{addr:016X}" for addr in skipped)
                QMessageBox.warning(
                    self, "Length Mismatch",
                    f"The following addresses were skipped — "
                    f"current memory length does not match the initial value:\n\n{skipped_strs}"
                )

    def _on_unfollow(self):
        from modding.debug_actions import debug_cache
        for item in self.values_list.selectedItems():
            addr = item.data(Qt.ItemDataRole.UserRole)
            debug_cache.pop(addr, None)
            self.values_list.takeItem(self.values_list.row(item))
        if self.values_list.count() == 0:
            self._stop_refresh()

    def _on_edit_values(self):
        dialog = _EditDialog(self)
        dialog.change_cached_value.clicked.connect(lambda: self._on_change_cached_value(dialog))
        dialog.exec()

    def _on_change_cached_value(self, dialog: "_EditDialog"):
        from modding.debug_actions import debug_edit
        new_value = dialog.value_input.text()
        if not new_value:
            return
        addrs = self._get_selected_addrs()
        if not addrs:
            return

        check_length = not self.dont_check_length.isChecked()
        result = ensure_exception(debug_edit, (addrs, new_value, check_length))
        if result is not None:
            patched, skipped = result
            if skipped and check_length:
                skipped_strs = "\n".join(f"0x{addr:016X}" for addr in skipped)
                QMessageBox.warning(
                    self, "Length Mismatch",
                    f"The following addresses were skipped — "
                    f"new value length does not match the initial value:\n\n{skipped_strs}"
                )
            dialog.accept()


class _EditDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Values")
        self.setFixedWidth(320)
        self.setStyleSheet(COMMON_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("New value")

        self.change_cached_value = QPushButton("Change")
        self.change_cached_value.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(QLabel("Enter new value:"))
        layout.addWidget(self.value_input)
        layout.addWidget(self.change_cached_value)
