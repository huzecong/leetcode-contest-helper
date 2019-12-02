from .base import CodeGen
from .cpp import CppCodeGen
from .python import PythonCodeGen

__all__ = [
    "create_codegen",
    "LANGUAGES",
]


def create_codegen(lang: str) -> CodeGen:
    return LANGUAGES[lang]()


LANGUAGES = {
    "cpp": CppCodeGen,
    "python": PythonCodeGen,
}
