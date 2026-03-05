from ..database.user.user_variables import user_variables


def check_game_executable():
    if user_variables.game_executable == None:
        from ..io.input.select_game_exec import select_game_exec
        select_game_exec()