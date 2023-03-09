def pipenv_run(cmd_list: list) -> list:
    return ["pipenv", "run"] + cmd_list
