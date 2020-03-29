import abc
import os
import shutil
import traceback
from datetime import datetime
from typing import Dict, Iterable, List, Tuple, TypeVar, Union

from lchelper.common import *
from lchelper.logging import log
from lchelper.parser import parse_problem

__all__ = [
    "Code",
    "Signature",
    "CodeGen",
]

T = TypeVar('T')
Signature = Union[ProblemSignature, InteractiveProblemSignature]
Code = List[str]


class CodeGen(abc.ABC):
    @property
    @abc.abstractmethod
    def language(self) -> str:
        r"""Name of the language to generate."""
        raise NotImplementedError

    @property
    def extra_files(self) -> Dict[str, str]:
        r"""Extra files that will be written verbatim under the project folder. The returned dictionary maps file names
        to raw code.
        """
        return {}

    @property
    @abc.abstractmethod
    def code_extension(self) -> str:
        r"""The file extension for code files."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def line_comment_symbol(self) -> str:
        r"""The symbol for starting a line comment."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def template_code(self) -> str:
        r"""The template code for each problem. Should include section markers for:

        - ``SOLUTION CLASS``: the section to insert the solution class.
        - ``SUBMIT``: the section to submit to LeetCode.
        - ``USER TEMPLATE``: the section to insert user-defined template code.
        - ``TEST``: the section to insert testing code.

        Optionally, the following section markers can be included:

        - ``STATEMENTS``: the section to insert problem statements.
        """
        raise NotImplementedError

    @property
    def user_template_code(self) -> str:
        r"""User-defined templates for convenience. These will be included in the submission."""
        return ""

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

    def replace_section(self, code: Code, replacements: Dict[str, Code], *, ignore_errors: bool = False) -> Code:
        r"""Replace a section of template with actual code. Sections are often marked with line comments.

        :param code: The code as a list of strings, one per line.
        :param replacements: A dictionary mapping section names to replacement code.
        :param ignore_errors: A :exc:`ValueError` will be thrown for sections that are not found, unless this argument
            is ``True``. Defaults to ``False``.
        :return: The updated code.
        """
        for section_name, section_code in replacements.items():
            try:
                start_line = code.index(f"{self.line_comment_symbol} BEGIN {section_name}")
                end_line = code.index(f"{self.line_comment_symbol} END {section_name}", start_line + 1)
                # exclude the line comments
                code = code[:start_line] + section_code + code[(end_line + 1):]
            except ValueError:
                if not ignore_errors:
                    raise ValueError(f"Section '{section_name}' not found in template code for {self.language} "
                                     f"({self.__class__!r})")
        return code

    @classmethod
    def list_join(cls, list_xs: Iterable[List[T]], sep: List[T]) -> List[T]:
        ret = []
        for idx, xs in enumerate(list_xs):
            if idx > 0:
                ret.extend(sep)
            ret.extend(xs)
        return ret

    @abc.abstractmethod
    def generate_code(self, problem: Problem, signature: Signature) -> Tuple[Code, Code]:
        r"""Generate code given the signature. Code consists of two parts:

        - Code for the solution class. This is basically the template as-is.
        - Code for testing the solution. This includes test functions for each example, and also the main function where
          the test functions are called and results are compared.

        :param problem: The crawled raw description of the problem.
        :param signature: The parsed signature of the problem.
        :return: A tuple of two lists of strings, corresponding to code for the solution class, and code for testing.
        """
        raise NotImplementedError

    def generate_additional_files(self, project_path: str, problems: List[Problem],
                                  signatures: List[Signature]) -> None:
        r"""Generate additional files that the project requires, besides those in :attr:`EXTRA_FILES` that are written
        verbatim.

        :param project_path: Path to the project folder.
        :param problems: List of problem descriptions to generate code for.
        :param signatures: Parsed signatures of problems.
        """
        pass

    def get_problem_file_name(self, idx: int, problem: Problem) -> str:
        r"""Generate the code file name for a problem. By default, names are uppercase letters starting from "A".

        :param idx: Zero-based index of the problem.
        :param problem: The description of the problem.
        :return: The code file name of the problem.
        """
        return f"{chr(ord('A') + idx)}{self.code_extension}"

    def format_statement(self, problem: Problem) -> List[str]:
        r"""Convert the problem statement into code (as comments).

        :param problem: The problem description.
        :return: Code for the problem statement.
        """
        statement = []
        max_length = 80 - (len(self.line_comment_symbol) + 1)
        for line in problem.statement.strip().split("\n"):
            comments = [f"{self.line_comment_symbol} {line[i:(i + max_length)]}"
                        for i in range(0, len(line), max_length)]
            statement.extend(comments)
        return statement

    def create_project(self, project_path: str, problems: List[Problem], site: str, debug: bool = False) -> None:
        r"""Create the folder for the project and generate code and supporting files.

        :param project_path: Path to the project folder.
        :param problems: List of problem descriptions to generate code for.
        :param site: The LeetCode site where problems are crawled. Different sites may have slightly different syntax
            (or language-dependent markings).
        :param debug: If ``True``, exceptions will not be caught. This is probably only useful when the ``--debug``
            flag is set, in which case the Python debugger is hooked to handle exceptions.
        """
        if not os.path.exists(project_path):
            os.makedirs(project_path)
        template = self.template_code.strip().split("\n")
        user_template = self.user_template_code.strip().split("\n")
        template = self.replace_section(template, {"USER TEMPLATE": user_template})

        signatures = []
        for idx, problem in enumerate(problems):
            try:
                problem_signature = parse_problem(problem, site)
                signatures.append(problem_signature)
                solution_code, test_code = self.generate_code(problem, problem_signature)
                problem_code = self.replace_section(template, {
                    "SOLUTION CLASS": solution_code,
                    "TEST": test_code,
                })
                if problem.statement != "":
                    statement = self.format_statement(problem)
                    problem_code = self.replace_section(problem_code, {"STATEMENT": statement}, ignore_errors=True)
                code_path = os.path.join(project_path, self.get_problem_file_name(idx, problem))
                self.write_and_backup(code_path, "\n".join(problem_code) + "\n")
            except Exception:
                if debug:
                    raise
                traceback.print_exc()
                log(f"Exception occurred while processing \"{problem.name}\"", "error")

        for tmpl_name, tmpl_code in self.extra_files.items():
            with open(os.path.join(project_path, tmpl_name), "w") as f:
                f.write(tmpl_code.strip() + "\n")

        self.generate_additional_files(project_path, problems, signatures)
