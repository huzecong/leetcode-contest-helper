from typing import Any, Dict, List, NamedTuple, Optional, Tuple

__all__ = [
    "User",
    "Problem",
    "FunctionSignature",
    "Example",
    "ProblemSignature",
    "Interaction",
    "InteractiveProblemSignature",
]


class User(NamedTuple):
    username: str
    site: str  # "leetcode" or "leetcode-cn"

    def __repr__(self):
        if self.site == "leetcode":
            return self.username
        return f"{self.username} ({self.site})"


class Problem(NamedTuple):
    r"""Raw description of the problem crawled from the web page."""
    url: str
    name: str
    statement: str  # problem statement, including examples and constraints
    examples: List[str]  # raw examples, consisting of inputs and outputs (and potentially explanations)
    code: List[str]  # template code, in lines


class FunctionSignature(NamedTuple):
    r"""Signature of a function."""
    name: str
    arguments: List[Tuple[str, str]]  # list of (type, name)
    return_type: str


class Example(NamedTuple):
    r"""An example test case, consisting of an input--output pair."""
    input: Dict[str, Any]
    output: Any


class ProblemSignature(NamedTuple):
    r"""Signature of a problem, including the function signature and test cases."""
    function: FunctionSignature
    examples: List[Example]


class Interaction(NamedTuple):
    r"""An "interaction" in interactive problems. An example test case for interactive problems consist of multiple
    "interactions", where each interaction calls a specific function, and (potentially) expects an output.
    """
    function: str
    input: Dict[str, Any]
    output: Optional[Any]


class InteractiveProblemSignature(NamedTuple):
    r"""Signature of an interactive problem."""
    class_name: str
    functions: List[FunctionSignature]
    examples: List[List[Interaction]]
