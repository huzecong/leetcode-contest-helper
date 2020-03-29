import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union

from lchelper.codegen.base import Code, CodeGen, Signature
from lchelper.common import *
from lchelper.utils import remove_affix

__all__ = [
    "PythonCodeGen",
]


class PythonCodeGen(CodeGen):
    @property
    def language(self) -> str:
        return "Python"

    @property
    def code_extension(self) -> str:
        return ".py"

    @property
    def line_comment_symbol(self) -> str:
        return "#"

    @property
    def template_code(self) -> str:
        return r"""
from typing import *

class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None

# BEGIN SUBMIT

# BEGIN USER TEMPLATE

# END USER TEMPLATE

# BEGIN SOLUTION CLASS

# END SOLUTION CLASS

# END SUBMIT

# BEGIN STATEMENT

# END STATEMENT


def _construct_tree(parent: List[Optional[int]]) -> Optional[TreeNode]:
    from queue import Queue
    q: 'Queue[TreeNode]' = Queue()
    ptr = 0

    def _add_node() -> Optional[TreeNode]:
        nonlocal ptr
        if ptr >= len(parent):
            return None
        val = parent[ptr]
        ptr += 1
        if val is None:
            return None
        p = TreeNode(val)
        q.put(p)
        return p

    root = _add_node()
    while not q.empty():
        p = q.get()
        p.left = _add_node()
        p.right = _add_node()
    return root


def evaluate(msg: str, a, b):
    if a == b:
        print(f"{msg} [OK]")
    else:
        print(f"{msg} [WRONG]")
        print(f"Expected: {a!r}")
        print(f"Received: {b!r}")


# BEGIN TEST

# END TEST
"""

    TYPE_MAP = {
        "string": "str",
        "double": "float",
        "long long": "int",
        "unsigned int": "int",
        "unsigned long long": "int",
        "void": "None",
    }

    def _convert_cpp_type(self, type_name: str) -> str:
        type_name = type_name.strip().rstrip("*&")
        if type_name.startswith("vector<") and type_name.endswith(">"):
            inner_type_name = type_name[len("vector<"):-len(">")]
            return f"List[{self._convert_cpp_type(inner_type_name)}]"
        return self.TYPE_MAP.get(type_name, type_name)

    def generate_solution_code(self, signature: Signature) -> Code:
        if isinstance(signature, InteractiveProblemSignature):
            class_name = signature.class_name
            functions = signature.functions
        else:
            class_name = "Solution"
            functions = [signature.function]
        fn_codes = []
        for func_sig in functions:
            args = "".join(f", {arg_name}: {self._convert_cpp_type(arg_type)}"
                           for arg_type, arg_name in func_sig.arguments)
            if func_sig.name == class_name:
                fn_code = [
                    f"    def __init__(self{args}):",
                    f"        pass"]
            else:
                fn_code = [
                    f"    def {func_sig.name}(self{args}) -> {self._convert_cpp_type(func_sig.return_type)}:",
                    f"        pass"]
            fn_codes.append(fn_code)
        code = [f"class {class_name}:"] + self.list_join(fn_codes, [""])
        return code

    def generate_code(self, problem: Problem, signature: Signature) -> Tuple[Code, Code]:
        # Convert C++ code to Python code.
        solution_code = self.generate_solution_code(signature)

        def to_str(val: Any) -> str:
            if isinstance(val, list):
                return "[" + ", ".join(to_str(x) for x in val) + "]"
            if isinstance(val, str):
                return f'"{val}"'
            if isinstance(val, bool):  # bool is a subtype of int
                return "True" if val else "False"
            if isinstance(val, (int, float)):
                return str(val)
            assert False

        def to_tree(parent: List[Optional[int]]) -> str:
            return f"_construct_tree([{', '.join('None' if x is None else str(x) for x in parent)}])"

        def to_val(val: Any, type_name: str) -> str:
            if self._convert_cpp_type(type_name) == "TreeNode":
                return to_tree(val)
            return to_str(val)

        def to_args(input: Dict[str, Any], func_sig: FunctionSignature) -> List[str]:
            # Return list of assignments.
            assignments = []
            for type_name, arg_name in func_sig.arguments:
                assignments.append(assign(f"{func_sig.name}_{arg_name}", to_val(input[arg_name], type_name)))
            return assignments

        def call(func_name: str, args: List[str]) -> str:
            return f"{func_name}({', '.join(args)})"

        def ctor(class_name: str, obj_name: str, args: List[str]) -> str:
            return f"{obj_name} = {call(class_name, args)}"

        def assign(obj_name: str, value: str) -> str:
            return f"{obj_name} = {value}"

        # Generate test code as a function per example.
        test_functions = []
        instance_name = "_sol"
        if isinstance(signature, InteractiveProblemSignature):
            func_map: Dict[str, FunctionSignature] = {func_sig.name: func_sig for func_sig in signature.functions}
            for idx, example in enumerate(signature.examples):
                statements = []
                for ex_idx, ex in enumerate(example):
                    func_sig = func_map[ex.function]
                    statements.extend(to_args(ex.input, func_sig))
                    args = [f"{func_sig.name}_{arg_name}" for _, arg_name in func_sig.arguments]
                    if ex.function == signature.class_name:
                        ctor_stmt = ctor(signature.class_name, instance_name, args)
                        statements.append(ctor_stmt)
                    else:
                        ret_name = f"_ret{ex_idx}"
                        if func_sig.return_type != "void":
                            ret_ans_var = f"_ret_ans{ex_idx}"
                            stmts = [
                                assign(ret_ans_var, to_val(ex.output, func_sig.return_type)),
                                assign(ret_name, f"{instance_name}.{call(ex.function, args)}"),
                                call("evaluate", [to_str(f"{problem.name} - Example {idx} - Interaction {ex_idx}"),
                                                  ret_ans_var, ret_name]),
                            ]
                            statements.extend(stmts)
                        else:
                            stmt = f"{instance_name}.{call(ex.function, args)}"
                            statements.append(stmt)
                test_fn = [
                    f"def eval_example_{idx}():",
                    *["    " + line for line in statements]]
                test_functions.append(test_fn)

            main_code = [
                "def main():",
                *["    " + f"eval_example_{idx}()" for idx in range(len(signature.examples))],
                "",
                "",
                "if __name__ == '__main__':",
                "    main()"]
        else:
            func_sig = signature.function
            for idx, example in enumerate(signature.examples):
                statements = []
                for type_name, arg_name in func_sig.arguments:
                    stmt = assign(arg_name, to_val(example.input[arg_name], type_name))
                    statements.append(stmt)
                args = [arg_name for _, arg_name in func_sig.arguments]
                ret_name = "_ret"
                ret_ans_var = "_ret_ans"
                stmts = [
                    assign(ret_ans_var, to_val(example.output, func_sig.return_type)),
                    assign(ret_name, f"{instance_name}.{call(func_sig.name, args)}"),
                    call("evaluate", [to_str(f"{problem.name} - Example {idx}"), ret_ans_var, ret_name]),
                ]
                statements.extend(stmts)

                test_fn = [
                    f"def eval_example_{idx}(_sol: Solution):",
                    *["    " + line for line in statements]]
                test_functions.append(test_fn)

            main_code = [
                "def main():",
                "    _sol = Solution()",
                *[f"    eval_example_{idx}(_sol)" for idx in range(len(signature.examples))],
                "",
                "",
                "if __name__ == '__main__':",
                "    main()"]

        test_code = self.list_join(test_functions + [main_code], ["", ""])
        return solution_code, test_code
