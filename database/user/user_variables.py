import json, os

from core.variable_manager import ProgramVariables

class UserVariables():
    from error_handler.ensure_exception import ensure_exception

    def get_game_executable(self, path=ProgramVariables.__memory_json__):
        with open(path, 'r') as f:
            return json.load(f)["game_executable"]

    def set_game_executable(self):
        from core.automatic_processes.find_game_executable import find_game_executable
        auto_game_executable = find_game_executable()

        from file_io.output.edit_json import edit_json
        if auto_game_executable is not None:
            edit_json(ProgramVariables.__memory_json__, auto_game_executable)

            self.game_executable = auto_game_executable

        if self.game_executable is None:
            from PySide6.QtWidgets import QMessageBox as _QMB
            from ui.main_page import MainPage as _MainPage

            _QMB.warning(_MainPage.main_page, "Game Executable Not Found", "Please select your game executable manually")

            while self.game_executable == None:
                from file_io.input.select_game_exec import select_game_exec
                edit_json(ProgramVariables.__memory_json__, select_game_exec())

                self.game_executable = self.get_game_executable()

    def __init__(self):
        self.game_executable = self.ensure_exception(self.get_game_executable, ())

        if self.game_executable is None:
            self.ensure_exception(self.set_game_executable, ())

        self.game_dir = os.path.dirname(self.game_executable)
        self.mod_dir = os.path.join(self.game_dir, "Documents", "res", "mod")
        self.game_logs = os.path.join(self.game_dir, "log.txt")

user_variables = UserVariables()