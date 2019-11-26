import abc
import os
import shutil
from datetime import datetime
from typing import Union, Tuple, List

from lchelper.common import *
from lchelper.logging import log

__all__ = [
    "CodeGen",
]


class CodeGen(abc.ABC):
    @classmethod
    def write_and_backup(cls, path: str, contents: str) -> None:
        r"""Check if there is already a file at the given path, create a backup if there is, and then write contents to
        the file.
        """
        if os.path.exists(path):
            with open(path, "r") as f:
                original_contents = f.read()
            if original_contents != contents:
                # Only create backup if contents differ.
                creation_time = os.path.getctime(path)
                timestamp = datetime.fromtimestamp(creation_time).strftime("%Y%m%d_%H%M%S")

                file_name, file_ext = os.path.splitext(path)
                dest_path = f"{file_name}_{timestamp}{file_ext}"
                shutil.move(path, dest_path)
                log(f"File '{path}' is modified, backup created at '{dest_path}'", "warning")
        with open(path, "w") as f:
            f.write(contents)

    @classmethod
    @abc.abstractmethod
    def generate_code(cls, problem: Problem, signature: Union[ProblemSignature, InteractiveProblemSignature]) \
            -> Tuple[str, str]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def create_project(cls, project_path: str, problems: List[Problem]) -> None:
        raise NotImplementedError
