import os
FLAGS_DIR = "./"
def _flag_path(filename: str) -> str:
    return os.path.join(FLAGS_DIR, filename)
def write_kill_flag() -> None:
    with open(_flag_path(".kill_flag"), "w") as f:
        f.write("KILL")
def check_kill_flag() -> bool:
    return os.path.exists(_flag_path(".kill_flag"))
def remove_kill_flag() -> None:
    path = _flag_path(".kill_flag")
    if os.path.exists(path):
        os.remove(path)
def write_purge_flag() -> None:
    with open(_flag_path("PURGE_NOW.flag"), "w") as f:
        f.write("PURGE")
def check_purge_flag() -> bool:
    return os.path.exists(_flag_path("PURGE_NOW.flag"))
def remove_purge_flag() -> None:
    path = _flag_path("PURGE_NOW.flag")
    if os.path.exists(path):
        os.remove(path)
def write_retain_flag() -> None:
    with open(_flag_path("RETAIN_DATA.flag"), "w") as f:
        f.write("RETAIN")
def check_retain_flag() -> bool:
    return os.path.exists(_flag_path("RETAIN_DATA.flag"))
def remove_retain_flag() -> None:
    path = _flag_path("RETAIN_DATA.flag")
    if os.path.exists(path):
        os.remove(path)
