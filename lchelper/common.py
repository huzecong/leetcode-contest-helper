from typing import Any, Dict, List, NamedTuple, Optional, Tuple, TypeVar, Type

__all__ = [
    "Problem",
    "FunctionSignature",
    "Example",
    "ProblemSignature",
    "Interaction",
    "InteractiveProblemSignature",
    "to_dict",
    "from_dict",
]


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


def to_dict(nm_tpl: NamedTuple) -> Dict[str, Any]:
    return nm_tpl._asdict()


TupleType = TypeVar('TupleType', bound=NamedTuple)


def from_dict(tpl_class: Type[TupleType], d: Dict[str, Any]) -> TupleType:
    assert all(field in d for field in tpl_class._fields)
    return tpl_class(**d)
