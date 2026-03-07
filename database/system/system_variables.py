import json

from core.variable_manager import ProgramVariables

class SystemVariables():
    def load_settings(self, path=ProgramVariables.__system_variables_json__):
        with open(path, 'r') as f:
            return json.load(f)
        
    def __init__(self):
        system_variables = SystemVariables.load_settings(self)
        self.version = system_variables["version"]
        self.dev_mode = True # It's not managed by settings.json due to security measures
        
system_variables = SystemVariables()