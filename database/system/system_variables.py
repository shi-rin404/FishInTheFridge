import json

from core.variable_manager import ProgramVariables

class SystemVariables():
    def load_settings(self, path=ProgramVariables.__system_variables_json__):
        with open(path, 'r') as f:
            return json.load(f)

    def __init__(self):
        system_variables = SystemVariables.load_settings(self)
        self.version = system_variables["version"]
        self.github_repo = system_variables.get("github_repo", "shi-rin404/FishInTheFridge")
        self.release_asset_prefix = system_variables.get("release_asset_prefix", "miyou-loader")
        self.dev_mode = True

system_variables = SystemVariables()
