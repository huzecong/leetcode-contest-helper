import time

from termcolor import colored

__all__ = [
    "log",
]

COLOR_MAP = {
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "info": "white",
}


def log(msg: str, level: str = "info") -> None:
    r"""Write a line of log with the specified logging level.

    :param msg: Message to log.
    :param level: Logging level. Available options are ``success``, ``warning``, ``error``, and ``info``.
    """
    if level not in COLOR_MAP:
        raise ValueError(f"Incorrect logging level '{level}'")
    # time_str = time.strftime("[%Y-%m-%d %H:%M:%S]")
    # print(colored(time_str, COLOR_MAP[level]), msg, flush=True)
    print(colored(msg, COLOR_MAP[level]), flush=True)
