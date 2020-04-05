import json
from typing import Any, Dict, List, Tuple, Union

from lchelper.common import *
from lchelper.logging import log

__all__ = [
    "parse_problem",
]


def parse_vardef(s: str) -> Tuple[str, str]:
    r"""Given a variable definition, return the type and identifier name. For instance:
    ``TreeNode *node`` should return ``TreeNode *`` and ``node``.

    :param s: The string to parse.
    :return: A tuple of (type, name).
    """
    s = s.strip()
    ident_start = next((idx for idx in range(len(s)) if s[idx:].isidentifier()), 0)
    # Identifier is the longest suffix that is a valid identifier.
    # If the entire definition is an identifier, it's a constructor and we count it as the type name.
    if ident_start == 0:
        type_name = s
        identifier = s
    else:
        type_name = s[:ident_start].strip()
        identifier = s[ident_start:].strip()
    return type_name, identifier


def find_functions(code: List[str]) -> Tuple[str, List[FunctionSignature]]:
    r"""Find functions in the solution class, and parse their signatures.

    :param code: Lines of the template code.
    :return: A tuple of two elements:
        - The class name (in most cases it's "Solution" but in interactive problems it might not).
        - A list of function signatures, indicating the functions in the solution class.
    """
    start_line = next(idx for idx in range(len(code)) if code[idx].startswith("class ") and code[idx].endswith(" {"))
    class_name = code[start_line][len("class "):-len(" {")].strip()
    end_line = code.index("};")
    signatures = []
    for line in code[(start_line + 1):end_line]:
        # A very heuristic way to find function beginnings.
        if line.startswith("    ") and line.endswith("{"):
            # Find function name.
            bracket_pos = line.find("(")
            return_type, func_name = parse_vardef(line[:bracket_pos])
            args_str = line[(bracket_pos + 1):line.find(")")].split(",")
            arguments = [parse_vardef(s) for s in args_str if s]
            signatures.append(FunctionSignature(func_name, arguments, return_type))
    return class_name, signatures


def parse_value(s: str) -> Tuple[Any, str]:
    r"""Parse a JSON value from the string, and return the remaining part of the string.

    :return: A tuple of (parsed JSON object, remaining unparsed string).
    """
    try:
        obj = json.loads(s)
        ret_str = ""
    except json.JSONDecodeError as e:
        obj = json.loads(s[:e.pos])
        ret_str = s[e.pos:]
    return obj, ret_str.strip()


def parse_problem(problem: Problem, site: str = "leetcode") -> Union[ProblemSignature, InteractiveProblemSignature]:
    r"""Parse the problem given the raw contents crawled from the web.
    """

    def find_example_section(s: str, cur_tag: str, next_tag: str, colon: str = ":", ignore_error: bool = False) -> str:
        r"""Find the part in the example that is between two tags. If ``next_tag`` does not exist, then find the part
        until the end.
        """
        start_pos = s.find(cur_tag)
        if start_pos == -1:
            if not ignore_error:
                raise ValueError
            start_pos = 0
        else:
            start_pos += len(cur_tag)
            if s[start_pos] == colon:
                start_pos += 1
        end_pos = s.find(next_tag, start_pos)
        if end_pos == -1:
            if not ignore_error:
                raise ValueError
            end_pos = len(s)
        return s[start_pos:end_pos].strip()

    # Parse function signature from code.
    class_name, func_signatures = find_functions(problem.code)
    assert len(func_signatures) > 0
    if len(func_signatures) > 1:
        # Probably an interactive problem, skip for now.
        func_map: Dict[str, FunctionSignature] = {signature.name: signature for signature in func_signatures}
        examples: List[List[Interaction]] = []
        for example in problem.examples:
            try:
                input_str = find_example_section(example, "输入", "输出", "：")
                output_str = find_example_section(example, "输出", "解释", "：")
            except ValueError:
                input_str = find_example_section(example, "Input", "Output", ignore_error=True)
                output_str = find_example_section(example, "Output", "Explanation", ignore_error=True)

            functions, input_str = parse_value(input_str)
            arg_vals, input_str = parse_value(input_str)
            if len(input_str) > 0:
                log(f"Problem \"{problem.name}\": Extra characters in example input section: {input_str}", "warning")
            ret_vals, output_str = parse_value(output_str)
            if len(output_str) > 0:
                log(f"Problem \"{problem.name}\": Extra characters in example output section: {output_str}", "warning")

            cur_examples = [
                Interaction(
                    function=func,
                    input={arg_name: val for (_, arg_name), val in zip(func_map[func].arguments, args)},
                    output=ret)
                for func, args, ret in zip(functions, arg_vals, ret_vals)
            ]
            examples.append(cur_examples)

        return InteractiveProblemSignature(class_name, func_signatures, examples)

    else:
        assert class_name == "Solution"

        func_signature = func_signatures[0]
        examples: List[Example] = []
        for ex_id, example in enumerate(problem.examples):
            try:
                input_str = find_example_section(example, "输入", "输出", "：")
                output_str = find_example_section(example, "输出", "解释", "：")
            except ValueError:
                input_str = find_example_section(example, "Input", "Output", ignore_error=True)
                output_str = find_example_section(example, "Output", "Explanation", ignore_error=True)

            input_vals = {}
            for idx, (_, name) in enumerate(func_signature.arguments):
                if idx > 0 and input_str.startswith(","):
                    input_str = input_str[1:].strip()
                if input_str[0].isidentifier():
                    ident_end = next((idx for idx in range(1, len(input_str))
                                      if not input_str[:idx].isidentifier()), len(input_str) + 1) - 1
                    ident = input_str[:ident_end]
                    if ident != name:
                        log(f"Problem \"{problem.name}\": Argument {idx + 1} should be `{name}`, "
                            f"but `{ident}` found in example {ex_id + 1}", "warning")
                    assert input_str.startswith(f"{ident} =")
                    input_str = input_str[len(f"{ident} ="):].strip()
                elif idx != 0:
                    log(f"Problem \"{problem.name}\": Argument {idx + 1} is unnamed in example {ex_id + 1}", "warning")
                input_val, input_str = parse_value(input_str)
                input_vals[name] = input_val
            if len(input_str) > 0:
                log(f"Problem \"{problem.name}\": Extra characters in example input section:\n{input_str}", "warning")

            output_val, output_str = parse_value(output_str)
            if len(output_str) > 0:
                log(f"Problem \"{problem.name}\": Extra characters in example output section:\n{output_str}", "warning")

            examples.append(Example(input_vals, output_val))

        return ProblemSignature(func_signature, examples)
