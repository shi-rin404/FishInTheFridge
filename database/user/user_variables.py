import json, os

from ...core.variable_manager import ProgramVariables

class UserVariables():
    def __get_game_executable__(self, path=ProgramVariables.__memory_json__):
        with open(path, 'r') as f:
            return json.load(f)["game_executable"]        

    def __init__(self):
        self.game_executable = self.__get_game_executable__
        self.game_dir = os.path.dirname(self.game_executable)

user_variables = UserVariables()