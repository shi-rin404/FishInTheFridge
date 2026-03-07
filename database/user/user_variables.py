import json, os

from core.variable_manager import ProgramVariables

class UserVariables():
    def __get_game_executable__(self, path=ProgramVariables.__memory_json__):
        with open(path, 'r') as f:
            return json.load(f)["game_executable"]        

    def __init__(self):
        self.game_executable = self.__get_game_executable__()
        while self.game_executable == None:
            from file_io.input.select_game_exec import select_game_exec
            select_game_exec()
            self.game_executable = self.__get_game_executable__()
        self.game_dir = os.path.dirname(self.game_executable)
        self.mod_dir = os.path.join(user_variables.game_dir, "Documents", "res", "mod")

user_variables = UserVariables()