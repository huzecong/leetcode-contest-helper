from .cpp import CppCodeGen

__all__ = [
    "cpp",
    "LANGUAGES",
]

LANGUAGES = {
    "cpp": CppCodeGen,
}
