import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union

from lchelper.codegen.base import Code, CodeGen, Signature
from lchelper.common import *
from lchelper.utils import remove_affix

__all__ = [
    "CppCodeGen",
]


class CppCodeGen(CodeGen):
    @property
    def language(self) -> str:
        return "C++"

    @property
    def code_extension(self) -> str:
        return ".cpp"

    @property
    def line_comment_symbol(self) -> str:
        return "//"

    @property
    def extra_files(self) -> Dict[str, str]:
        return {
            # A header-only library for comparing outputs.
            "_testing.h": r"""
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
""",
            # Boilerplate code for supporting LeetCode-specific constructs.
            "_boilerplate.hpp": r"""
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
#include <random>
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

#include "_testing.h"

using namespace std;


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

TreeNode *_construct_tree(const vector<int> &parent) {
    queue<TreeNode *> q;
    int ptr = 0;

    auto _add_node = [&]() -> TreeNode * {
        if (ptr >= parent.size()) return nullptr;
        int val = parent[ptr++];
        if (val == NONE) return nullptr;
        auto *p = new TreeNode(val);
        q.push(p);
        return p;
    };

    TreeNode *root = _add_node();
    while (!q.empty()) {
        if (ptr >= parent.size()) break;
        TreeNode *p = q.front();
        q.pop();
        p->left = _add_node();
        p->right = _add_node();
    }
    return root;
}

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
""",
        }

    @property
    def template_code(self) -> str:
        return r"""
#include "_boilerplate.hpp"

// BEGIN SUBMIT

// BEGIN USER TEMPLATE

// END USER TEMPLATE

// BEGIN SOLUTION CLASS

// END SOLUTION CLASS

// END SUBMIT

// BEGIN STATEMENT

// END STATEMENT

// BEGIN TEST

// END TEST
"""

    @property
    def user_template_code(self) -> str:
        return r"""
#ifndef LEETCODE_LOCAL
# define print(...)
# define PRINT(...)
# define debug(...)
#endif  // LEETCODE_LOCAL

typedef long long ll;
typedef unsigned int uint;

template <class T>
struct _greater : less<T> {
    inline bool operator() (const T& x, const T& y) const {
        return less<T>::operator()(y, x);
    }
};
template <class T>
using min_heap = priority_queue<T, vector<T>, _greater<T>>;
template <class T>
using max_heap = priority_queue<T, vector<T>, less<T>>;

inline double runtime() {
    return (double)clock() / CLOCKS_PER_SEC;
}

#define tget(a, b) get<b>(a)
"""

    def generate_code(self, problem: Problem, signature: Signature) -> Tuple[Code, Code]:
        # Generate solution code as the crawled template.
        solution_code = problem.code.copy()

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
                        if func_sig.return_type != "void":
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
                            stmt = f"{instance_name}.{call(ex.function, args)};"
                            statements.append(stmt)
                declarations = defaultdict(list)
                for func_sig in signature.functions:
                    for type_name, arg_name in func_sig.arguments:
                        declarations[type_name].append(f"{func_sig.name}_{arg_name}")
                test_fn = [
                    f"void test_example_{idx}() {{",
                    *["    " + decl(type_name, objs) for type_name, objs in declarations.items()],
                    *["    " + line for line in statements],
                    "}"]
                test_functions.append(test_fn)

            main_code = [
                "int main() {",
                *["    " + f"test_example_{idx}();" for idx in range(len(signature.examples))],
                "}"]
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

                test_fn = [
                    f"void test_example_{idx}(Solution &_sol) {{",
                    *["    " + line for line in statements],
                    "}"]
                test_functions.append(test_fn)

            main_code = [
                "int main() {",
                "    Solution _sol;",
                *[f"    test_example_{idx}(_sol);" for idx in range(len(signature.examples))],
                "}"]

        test_code = self.list_join(test_functions + [main_code], ["", ""])
        return solution_code, test_code

    def generate_additional_files(self, project_path: str, problems: List[Problem],
                                  signatures: List[Signature]) -> None:
        cmake = [
            "cmake_minimum_required(VERSION 3.12)",
            "project(leetcode)",
            "set(CMAKE_CXX_STANDARD 17)",
            'set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DLEETCODE_LOCAL")',
        ]
        for idx, problem in enumerate(problems):
            file_name = self.get_problem_file_name(idx, problem)
            exec_name = remove_affix(file_name, suffix=self.code_extension)
            cmake.append(f"add_executable({exec_name} {file_name})")
        with open(os.path.join(project_path, "CMakeLists.txt"), "w") as f:
            f.write("\n".join(cmake))
