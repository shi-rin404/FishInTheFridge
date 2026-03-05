from pathlib import Path

class ProgramVariables():    
    __memory_json__ = Path(__file__).parent.parent / "database" / "user" / "memory.json"
    __system_variables_json__ = Path(__file__).parent.parent / "database" / "system" / "system_variables.json"

program_variables = ProgramVariables()