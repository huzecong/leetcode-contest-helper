import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union

from lchelper.codegen.base import CodeGen
from lchelper.common import *
from lchelper.parser import parse_problem

__all__ = [
    "CppCodeGen",
]


class CppCodeGen(CodeGen):
    TESTING_H_CODE = r"""
#ifndef TESTING_H
#define TESTING_H

#include <iostream>
#include <vector>

template <typename T>
void print(const T &x) { std::cout << x; }

template <typename T>
void print(const std::vector<T> &vec) {
    for (int i = 0; i < vec.size(); ++i) {
        std::cout << (i == 0 ? "{" : ", ");
        print(vec[i]);
    }
    std::cout << "}";
}

template <>
void print(const bool &x) { std::cout << (x ? "true" : "false"); }

template <typename T>
inline bool _test(const T &a, const T &b) {
    return a == b;
}

template <typename T>
inline bool _test(const std::vector<T> &a, const std::vector<T> &b) {
    if (a.size() != b.size()) return false;
    for (int i = 0; i < a.size(); ++i)
        if (!_test(a[i], b[i])) return false;
    return true;
}

template <typename T>
inline void test(const char *msg, const T &a, const T &b) {
    if (_test(a, b)) {
        std::cout << msg << " [OK]" << std::endl;
    } else {
        std::cout << msg << " [WRONG]" << std::endl;
        std::cout << "Expected: ";
        print(a);
        std::cout << std::endl << "Received: ";
        print(b);
        std::cout << std::endl;
    }
}

#endif  // TESTING_H
"""

    TEMPLATE_CODE = r"""
#include <algorithm>
#include <bitset>
#include <complex>
#include <fstream>
#include <functional>
#include <iomanip>
#include <ios>
#include <iostream>
#include <map>
#include <numeric>
#include <queue>
#include <set>
#include <stack>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include <cmath>
#include <climits>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>

#include "testing.h"

using namespace std;

#ifdef LEETCODE_LOCAL

template <typename T>
void print(T *a, int n) {
    for (int i = 1; i < n; ++i)
        std::cout << a[i] << " ";
    std::cout << a[n] << std::endl;
}

#define PRINT(__l, __r, __s, __t) {                     \
    std::cout << #__l #__s << "~" << #__t #__r << ": "; \
    for (auto __i = __s; __i != __t; ++__i)             \
        std::cout << __l __i __r << " ";                \
    std::cout << std::endl;                             \
}

template <typename ...Args>
void debug(Args ...args);

template <>
void debug() { std::cout << std::endl; }

template <typename T, typename ...Args>
void debug(const T &x, Args ...args) {
    print(x);
    std::cout << " ";
    debug(args...);
}

#endif  // LEETCODE_LOCAL

struct TreeNode {
    int val;
    TreeNode *left;
    TreeNode *right;
    TreeNode(int x) : val(x), left(NULL), right(NULL) {}
    ~TreeNode() {
        if (left != NULL) delete left;
        if (right != NULL) delete right;
    }
};

const int NONE = INT_MIN;

TreeNode *_construct_tree(const vector<int> &parent, int idx = 0) {
    if (idx >= parent.size() || parent[idx] == NONE) return NULL;
    TreeNode *root = new TreeNode(parent[idx]);
    root->left = _construct_tree(parent, idx * 2 + 1);
    root->right = _construct_tree(parent, idx * 2 + 2);
    return root;
}

// BEGIN SUBMIT

typedef long long ll;
typedef unsigned int uint;
template <class T>
using heap = priority_queue<T, vector<T>, greater<T>>;

inline double runtime() {
    return (double)clock() / CLOCKS_PER_SEC;
}

#ifndef LEETCODE_LOCAL
# define print(...)
# define PRINT(...)
# define debug(...)
#endif  // LEETCODE_LOCAL

#define tget(a, b) get<b>(a)

// BEGIN SOLUTION CLASS

// END SOLUTION CLASS

// END SUBMIT

// BEGIN TEST

// END TEST
"""

    @classmethod
    def generate_code(cls, problem: Problem, signature: Union[ProblemSignature, InteractiveProblemSignature]) \
            -> Tuple[str, str]:
        r"""Generate code given the signature. Code consists of two parts:

        - Code for the solution class. This is basically the template as-is, but could also include the statement in
          comments.
        - Code for testing the solution. This includes test functions for each example, and also the main function where
          the test functions are called and results are compared.

        :return: A tuple of two lists of strings, corresponding to code for the solution class, and code for testing.
        """
        # Generate solution code as the crawled template and (potentially) the statement in comments.
        solution_code = '\n'.join(problem.code)
        if len(problem.statement) > 0:
            statement = ["// " + line for line in problem.statement.split('\n')]
            solution_code = '\n'.join(statement) + "\n\n" + solution_code

        def to_str(val: Any) -> str:
            if isinstance(val, list):
                return "{" + ", ".join(to_str(x) for x in val) + "}"
            if isinstance(val, str):
                if len(val) == 1:
                    return f"'{val}'"
                return f'"{val}"'
            if isinstance(val, bool):  # bool is a subtype of int
                return "true" if val else "false"
            if isinstance(val, (int, float)):
                return str(val)
            assert False

        def to_tree(parent: List[Optional[int]]) -> str:
            return f"_construct_tree({{{', '.join('NONE' if x is None else str(x) for x in parent)}}})"

        def to_val(val: Any, type_name: str) -> str:
            if type_name.replace(' ', '') == "TreeNode*":
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
            return f"{class_name} {call(obj_name, args)};"

        def remove_cv_ref(typ: str) -> str:
            while True:
                if typ.startswith("const"):
                    typ = typ[len("const"):]
                elif typ.startswith("volatile"):
                    typ = typ[len("volatile"):]
                elif typ.endswith("&"):
                    typ = typ[:-1]
                else:
                    break
                typ = typ.strip()
            return typ

        def decl(type_name: str, obj_name: Union[str, List[str]]) -> str:
            type_name = remove_cv_ref(type_name)
            if isinstance(obj_name, list):
                return f"{type_name} {', '.join(obj_name)};"
            return f"{type_name} {obj_name};"

        def assign(obj_name: str, value: str) -> str:
            return f"{obj_name} = {value};"

        def decl_assign(ret_type: str, obj_name: str, value: str) -> str:
            ret_type = remove_cv_ref(ret_type)
            return f"{ret_type} {obj_name} = {value};"

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
                        if func_sig.return_type is not None:
                            ret_ans_var = f"_ret_ans{ex_idx}"
                            stmts = [
                                decl_assign(func_sig.return_type, ret_ans_var, to_val(ex.output, func_sig.return_type)),
                                decl_assign(func_sig.return_type, ret_name,
                                            f"{instance_name}.{call(ex.function, args)}"),
                                call("test", [to_str(f"{problem.name} - Example {idx} - Interaction {ex_idx}"),
                                              ret_ans_var, ret_name]) + ";",
                            ]
                            statements.extend(stmts)
                        else:
                            stmt = call(ex.function, args) + ";"
                            statements.append(stmt)
                declarations = defaultdict(list)
                for func_sig in signature.functions:
                    for type_name, arg_name in func_sig.arguments:
                        declarations[type_name].append(f"{func_sig.name}_{arg_name}")
                test_fn = '\n'.join([
                    f"void test_example_{idx}() {{",
                    *["    " + decl(type_name, objs) for type_name, objs in declarations.items()],
                    *["    " + line for line in statements],
                    "}"])
                test_functions.append(test_fn)

            main_code = '\n'.join([
                "int main() {",
                *["    " + f"test_example_{idx}();" for idx in range(len(signature.examples))],
                "}"])
        else:
            func_sig = signature.function
            for idx, example in enumerate(signature.examples):
                statements = []
                for type_name, arg_name in func_sig.arguments:
                    stmt = decl_assign(type_name, arg_name, to_val(example.input[arg_name], type_name))
                    statements.append(stmt)
                args = [arg_name for _, arg_name in func_sig.arguments]
                ret_name = "_ret"
                ret_ans_var = "_ret_ans"
                stmts = [
                    decl_assign(func_sig.return_type, ret_ans_var, to_val(example.output, func_sig.return_type)),
                    decl_assign(func_sig.return_type, ret_name, f"{instance_name}.{call(func_sig.name, args)}"),
                    call("test", [to_str(f"{problem.name} - Example {idx}"), ret_ans_var, ret_name]) + ";",
                ]
                statements.extend(stmts)

                test_fn = '\n'.join([
                    f"void test_example_{idx}(Solution &_sol) {{",
                    *["    " + line for line in statements],
                    "}"])
                test_functions.append(test_fn)

            main_code = '\n'.join([
                "int main() {",
                "    Solution _sol;",
                *[f"    test_example_{idx}(_sol);" for idx in range(len(signature.examples))],
                "}"])

        test_code = "\n\n".join(test_functions + [main_code])
        return solution_code, test_code

    @classmethod
    def create_project(cls, project_path: str, problems: List[Problem]) -> None:
        if not os.path.exists(project_path):
            os.makedirs(project_path)
        template = cls.TEMPLATE_CODE.strip().split("\n")
        solution_start_line = template.index("// BEGIN SOLUTION CLASS")
        solution_end_line = template.index("// END SOLUTION CLASS")
        test_start_line = template.index("// BEGIN TEST")
        test_end_line = template.index("// END TEST")

        file_names = [chr(ord('A') + idx) for idx in range(len(problems))]
        for idx, problem in enumerate(problems):
            problem_signature = parse_problem(problem)
            solution_code, test_code = cls.generate_code(problem, problem_signature)
            lines = "\n".join([
                "\n".join(template[:(solution_start_line + 1)]),
                solution_code,
                "\n".join(template[solution_end_line:(test_start_line + 1)]),
                test_code,
                "\n".join(template[test_end_line:])])
            code_path = os.path.join(project_path, f"{file_names[idx]}.cpp")
            cls.write_and_backup(code_path, lines + "\n")

        with open(os.path.join(project_path, "testing.h"), "w") as f:
            f.write(cls.TESTING_H_CODE)

        cmake = [
            "cmake_minimum_required(VERSION 3.12)",
            "project(leetcode)",
            "set(CMAKE_CXX_STANDARD 17)",
            'set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DLEETCODE_LOCAL")',
            *[f"add_executable({name} {name}.cpp)" for name in file_names],
        ]
        with open(os.path.join(project_path, "CMakeLists.txt"), "w") as f:
            f.write("\n".join(cmake))
