import os
import json
import fnmatch
from collections import defaultdict

from PySide6.QtWidgets import (
    QDialog, QMessageBox, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QTextBlockFormat

from database.user.user_variables import user_variables
from modding.character_lookup import (
    character_from_mod_manifest,
    load_character_keywords,
)


# ── JSON formatting ───────────────────────────────────────────

def _format_json_html(data: dict, conflict_keys: set[str]) -> str:
    """
    Format a dict as HTML with VSCode-style JSON colors.
    Keys in conflict_keys and their values are fully colored red.
    """
    C_KEY      = "#9CDCFE"
    C_STR      = "#CE9178"
    C_NUM      = "#B5CEA8"
    C_BOOL     = "#569CD6"
    C_PUNCT    = "#D4D4D4"
    C_CONFLICT = "#FF4444"
    Q = '"'

    def _esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _span(text: str, color: str) -> str:
        return f'<span style="color:{color}">{_esc(text)}</span>'

    def _fmt(v, depth: int, red: bool = False) -> str:
        pad = "  " * depth
        if isinstance(v, dict):
            if not v:
                return _span("{}", C_CONFLICT if red else C_PUNCT)
            parts = []
            items = list(v.items())
            for i, (k, val) in enumerate(items):
                entry_red = red or (depth == 0 and k in conflict_keys)
                key_color = C_CONFLICT if entry_red else C_KEY
                comma = _span(",", C_CONFLICT if entry_red else C_PUNCT) if i < len(items) - 1 else ""
                parts.append(
                    f"\n{pad}  {_span(Q + k + Q, key_color)}"
                    f"{_span(':', C_CONFLICT if entry_red else C_PUNCT)} "
                    f"{_fmt(val, depth + 1, red=entry_red)}{comma}"
                )
            open_b  = _span("{", C_CONFLICT if red else C_PUNCT)
            close_b = _span("}", C_CONFLICT if red else C_PUNCT)
            return open_b + "".join(parts) + f"\n{pad}" + close_b
        if isinstance(v, list):
            if not v:
                return _span("[]", C_CONFLICT if red else C_PUNCT)
            parts = []
            for i, item in enumerate(v):
                comma = _span(",", C_CONFLICT if red else C_PUNCT) if i < len(v) - 1 else ""
                parts.append(f"\n{pad}  {_fmt(item, depth + 1, red=red)}{comma}")
            open_b  = _span("[", C_CONFLICT if red else C_PUNCT)
            close_b = _span("]", C_CONFLICT if red else C_PUNCT)
            return open_b + "".join(parts) + f"\n{pad}" + close_b
        if isinstance(v, bool):
            return _span("true" if v else "false", C_CONFLICT if red else C_BOOL)
        if v is None:
            return _span("null", C_CONFLICT if red else C_BOOL)
        if isinstance(v, str):
            color = C_CONFLICT if red else C_STR
            return f'<span style="color:{color}">{Q}{_esc(v)}{Q}</span>'
        if isinstance(v, (int, float)):
            return _span(str(v), C_CONFLICT if red else C_NUM)
        return _span(str(v), C_CONFLICT if red else C_PUNCT)

    body = _fmt(data, 0)
    return (
        f'<pre style="background:#313131; color:#D4D4D4; '
        f'font-family:Consolas,monospace; font-size:12px; margin:0; padding:8px;">'
        f'{body}</pre>'
    )


# ── Overlap resolution dialog ─────────────────────────────────

class OverlapDialog(QDialog):
    def __init__(self,
                 left_file: str,  left_data: dict,
                 right_file: str, right_data: dict,
                 parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.result_choice = "left"
        self._drag_pos = QPoint()
        self._setup_ui(left_file, left_data, right_file, right_data)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _setup_ui(self, left_file, left_data, right_file, right_data):
        self.setStyleSheet("QDialog { background: #1E1E1E; } QLabel { background: transparent; }")
        self.resize(960, 540)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(10)

        title = QLabel("Overlapping Mods")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #FF4444; font-size: 18px; font-weight: bold;")
        root.addWidget(title)

        info = QLabel(
            f'Both files declare <span style="color:#FF4444;">name: '
            f'"{left_data.get("name", "")}"</span>. Choose which to keep.'
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #888888; font-size: 11px;")
        root.addWidget(info)

        cols = QHBoxLayout()
        cols.setSpacing(12)
        cols.addLayout(self._build_panel(left_file,  left_data,  align_right=False))
        cols.addLayout(self._build_panel(right_file, right_data, align_right=True))
        root.addLayout(cols)

    def _build_panel(self, filepath, data, align_right: bool) -> QVBoxLayout:
        side = "right" if align_right else "left"

        col = QVBoxLayout()
        col.setSpacing(6)

        label = QLabel(filepath)
        label.setStyleSheet("color: #666666; font-size: 10px;")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignRight if align_right else Qt.AlignmentFlag.AlignLeft)
        col.addWidget(label)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setStyleSheet("QTextEdit { background: #313131; border: 1px solid #3C3C3C; }")
        text.setFont(QFont("Consolas", 10))
        text.setHtml(_format_json_html(data, conflict_keys={"name"}))

        if align_right:
            cursor = text.textCursor()
            cursor.select(cursor.SelectionType.Document)
            fmt = QTextBlockFormat()
            fmt.setAlignment(Qt.AlignmentFlag.AlignRight)
            cursor.mergeBlockFormat(fmt)
            cursor.clearSelection()
            text.setTextCursor(cursor)

        col.addWidget(text, stretch=1)

        btn = QPushButton("Keep This Mod")
        btn.setStyleSheet(
            "QPushButton { background: #0078D4; color: white; padding: 8px 16px;"
            "              border: none; font-size: 13px; }"
            "QPushButton:hover   { background: #005A9E; }"
            "QPushButton:pressed { background: #004080; }"
        )
        btn.clicked.connect(lambda: (setattr(self, "result_choice", side), self.accept()))
        col.addWidget(btn)

        rename_btn = QPushButton("Rename This Mod")
        rename_btn.setStyleSheet(
            "QPushButton { background: #DEC539; color: white; padding: 8px 16px;"
            "              border: none; font-size: 13px; }"
            "QPushButton:hover   { background: #C9B030; }"
            "QPushButton:pressed { background: #A8922A; }"
        )
        rename_btn.clicked.connect(lambda: self._rename(filepath, data))
        col.addWidget(rename_btn)

        return col

    def _rename(self, filepath: str, data: dict):
        from PySide6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self, "Rename Mod",
            "Enter new name for this mod:",
            text=data.get("name", "")
        )
        if not ok or not new_name.strip():
            return
        data["name"] = new_name.strip()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.result_choice = "both"
        self.accept()


# ── Main ─────────────────────────────────────────────────────

def get_mods(reload_mod_combos_toggle:bool = True):    
    from core.variable_manager import program_variables
    import modding.path_dictionary as pd

    character_keywords = load_character_keywords()

    # 1. Walk mod_dir for all mod.json files (case-sensitive)
    mod_files: dict[str, dict] = {}
    for dirpath, _, filenames in os.walk(user_variables.mod_dir):
        for fname in filenames:
            if fnmatch.fnmatchcase(fname, "mod.json"):                
                path = os.path.join(dirpath, fname)                
                try:
                    with open(path, encoding="utf-8") as f:
                        mod_files[path] = json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    print(f"[get_mods] A(n) {type(e)} occurred when reading {path}")
                

    if not mod_files:
        pd.mod_dict.clear()
        pd.mod_character_dict.clear()
        pd.sync_character_group("mods", {})
        return

    # 2. Group files by their "name" value; files without "name" are ungrouped
    name_to_files: dict[str, list[str]] = defaultdict(list)
    nameless_files: list[str] = []

    for filepath, data in mod_files.items():
        name = data.get("name")
        if isinstance(name, str) and name:
            name_to_files[name].append(filepath)
        else:
            nameless_files.append(filepath)

    conflicting_names = {name for name, files in name_to_files.items() if len(files) > 1}

    # 3. Resolve each conflicting name pairwise
    # resolution value: single filepath (winner) or list of filepaths (rename resolved conflict)
    conflict_resolution: dict[str, str | list[str]] = {}

    if conflicting_names:
        n_dialogs = sum(len(name_to_files[n]) - 1 for n in conflicting_names)
        reply = QMessageBox.question(
            None,
            "Mod Conflicts Detected",
            f"<b>{len(conflicting_names)} mod name{'s' if len(conflicting_names) != 1 else ''}</b> "
            f"appear in multiple files.<br><br>"
            f"Would you like to resolve the {n_dialogs} conflict{'s' if n_dialogs != 1 else ''} manually?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for name in conflicting_names:
            files = name_to_files[name]
            winner = files[0]
            keep_both: list[str] = []
            for challenger in files[1:]:
                dlg = OverlapDialog(winner, mod_files[winner], challenger, mod_files[challenger])
                dlg.exec()
                if dlg.result_choice == "right":
                    winner = challenger
                elif dlg.result_choice == "both":
                    keep_both.extend([winner, challenger])
                    winner = None
                    break
            conflict_resolution[name] = keep_both if keep_both else winner

    # 4. Merge: discard "name" key from all entries; resolution takes priority for conflicts
    merged: dict = {}
    mod_characters: dict[str, str] = {}

    # Non-conflicting named files
    for name, files in name_to_files.items():
        if name not in conflicting_names:
            data = mod_files[files[0]]
            merged[name] = {k: v for k, v in data.items() if k != "name"}
            mod_characters[name] = character_from_mod_manifest(
                data,
                files[0],
                character_keywords,
            )

    # Resolved conflicts
    for resolution in conflict_resolution.values():
        filepaths = resolution if isinstance(resolution, list) else [resolution]
        for filepath in filepaths:
            data = mod_files[filepath]
            actual_name = data.get("name")
            if actual_name:
                merged[actual_name] = {k: v for k, v in data.items() if k != "name"}
                mod_characters[actual_name] = character_from_mod_manifest(
                    data,
                    filepath,
                    character_keywords,
                )

    # Files with no "name" key — skip; can't be keyed by name

    # 5. Update in-memory dict
    pd.mod_dict.clear()
    pd.mod_dict.update(merged)
    pd.mod_character_dict.clear()
    pd.mod_character_dict.update(mod_characters)
    pd.sync_character_group("mods", mod_characters)

    # 6. Persist to database
    os.makedirs(os.path.dirname(program_variables.mod_list_path), exist_ok=True)
    with open(program_variables.mod_list_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    # 7. Reload UI combos
    if reload_mod_combos_toggle:        
        _reload_mod_combos()


def _reload_mod_combos():
    from modding.update_ms_lists import update_ms_list
    from core.automatic_processes.update_comboboxes import update_comboboxes

    update_ms_list("mod")
    update_comboboxes("mod")
