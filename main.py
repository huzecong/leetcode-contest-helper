import getpass
import http.client
import http.cookiejar
import json
import os
import pickle
import shutil
import sys
import traceback
from collections import defaultdict
from enum import Enum, auto
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union, NewType

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def update_cookie(username, password):
    options = webdriver.ChromeOptions()
    # options.add_argument('--no-startup-window')
    browser = webdriver.Chrome(chrome_options=options)
    browser.set_window_position(0, 0)
    browser.set_window_size(800, 600)
    browser.switch_to.window(browser.window_handles[0])
    browser.get('https://leetcode.com/accounts/login/')
    browser.implicitly_wait(10)

    WebDriverWait(browser, 123456789).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'button[data-cy="sign-in-btn"]'))
    )

    elem = browser.find_element_by_css_selector('input[name="login"]')
    elem.clear()
    elem.send_keys(username)

    elem = browser.find_element_by_css_selector('input[type="password"]')
    elem.clear()
    elem.send_keys(password)

    print("User credentials filled")

    elem = browser.find_element_by_css_selector('button[data-cy="sign-in-btn"]')
    browser.execute_script("arguments[0].click();", elem)

    WebDriverWait(browser, 123456789).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'img.avatar'))
    )

    cookies = browser.get_cookies()
    jar = http.cookiejar.LWPCookieJar()
    for cookie in cookies:
        if cookie['name'] == 'WBStorage':
            continue
        jar.set_cookie(http.cookiejar.Cookie(
            version=0,
            name=cookie['name'],
            value=cookie['value'],
            port='80',
            port_specified=False,
            domain=cookie['domain'],
            domain_specified=True,
            domain_initial_dot=False,
            path=cookie['path'],
            path_specified=True,
            secure=cookie['secure'],
            expires=cookie.get('expiry', 0),
            discard=False,
            comment=None,
            comment_url=None,
            rest={}
        ))

    cookie_path = f'cookies/{username}.dat'
    jar.save(cookie_path, ignore_discard=True, ignore_expires=True)

    print(f'Cookies saved to `{cookie_path}`')

    browser.quit()


class Problem(NamedTuple):
    url: str
    name: str
    statement: str  # problem statement, including examples and constraints
    examples: List[str]  # raw examples, consisting of inputs and outputs (and potentially explanations)
    code: List[str]  # template code, in lines


def get_problems(contest_url: str) -> List[Problem]:
    browser = webdriver.Chrome()
    browser.set_window_position(0, 0)
    browser.set_window_size(800, 600)
    browser.switch_to.window(browser.window_handles[0])
    browser.implicitly_wait(10)
    browser.get(contest_url)

    cookie_jar = http.cookiejar.LWPCookieJar("cookies/huzecong.dat")
    cookie_jar.load(ignore_discard=True, ignore_expires=True)
    for c in cookie_jar:
        browser.add_cookie({"name": c.name, 'value': c.value, 'path': c.path, 'expiry': c.expires})

    elem = browser.find_element_by_css_selector("ul.contest-question-list")
    links = elem.find_elements_by_tag_name("a")
    problem_paths = [(link.get_attribute("href"), link.text) for link in links]

    parsed_problems = []
    for problem_url, problem_name in problem_paths:
        browser.get(problem_url)
        statement = browser.find_element_by_css_selector("div.question-content").text
        examples = [
            elem.text for elem in browser.find_elements_by_css_selector("pre:not([class])") if elem.text]
        code = [elem.text for elem in browser.find_elements_by_css_selector("pre.CodeMirror-line")]
        problem = Problem(problem_url, problem_name, statement, examples, code)
        parsed_problems.append(problem)

    return parsed_problems


class ProblemType(Enum):
    Normal = auto()
    Tree = auto()  # input is a tree, requires constructing `TreeNode` structures
    Interactive = auto()  # requires constructing the class and calling methods


class FunctionSignature(NamedTuple):
    name: str
    arguments: List[Tuple[str, str]]  # list of (type, name)
    return_type: str


class Example(NamedTuple):
    input: Dict[str, Any]
    output: Any


class ProblemSignature(NamedTuple):
    function: FunctionSignature
    examples: List[Example]


class InteractiveExample(NamedTuple):
    function: str
    input: Dict[str, Any]
    output: Optional[Any]


class InteractiveProblemSignature(NamedTuple):
    class_name: str
    functions: List[FunctionSignature]
    examples: List[List[InteractiveExample]]


def parse_vardef(s: str) -> Tuple[str, str]:
    r"""Given a variable definition, return the type and identifier name. For instance:
    ``TreeNode *node`` should return ``TreeNode *`` and ``node``.

    :param s: The string to parse.
    :return: A tuple of (type, name).
    """
    s = s.strip()
    type_end = next((idx for idx in range(len(s) - 1, -1, -1) if not s[idx].isidentifier()), -1)
    # In case there's no type (e.g., constructor), `type_end` will be -1, so `type_name` will be empty string.
    identifier = s[(type_end + 1):].strip()
    type_name = s[:(type_end + 1)].strip()
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
            arguments = [parse_vardef(s) for s in args_str]
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


def parse_problem(problem: Problem) -> Union[ProblemSignature, InteractiveProblemSignature]:
    r"""Parse the problem given the raw contents crawled from the web.
    """

    def find_example_section(s: str, cur_tag: str, next_tag: str) -> str:
        r"""Find the part in the example that is between two tags. If ``next_tag`` does not exist, then find the part
        until the end.
        """
        start_pos = s.find(cur_tag) + len(cur_tag)
        end_pos = s.find(next_tag, start_pos)
        if end_pos == -1:
            return s[start_pos:].strip()
        return s[start_pos:end_pos].strip()

    # Parse function signature from code.
    class_name, func_signatures = find_functions(problem.code)
    assert len(func_signatures) > 0
    if len(func_signatures) > 1:
        # Probably an interactive problem, skip for now.
        func_map: Dict[str, FunctionSignature] = {signature.name: signature for signature in func_signatures}
        examples: List[List[InteractiveExample]] = []
        for example in problem.examples:
            input_str = find_example_section(example, "Input", "Output")
            output_str = find_example_section(example, "Output", "Explanation")

            functions, input_str = parse_value(input_str)
            arg_vals, input_str = parse_value(input_str)
            assert len(input_str) == 0
            ret_vals, output_str = parse_value(output_str)
            assert len(output_str) == 0

            cur_examples = [
                InteractiveExample(
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
        for example in problem.examples:
            input_str = find_example_section(example, "Input:", "Output:")
            output_str = find_example_section(example, "Output:", "Explanation:")

            input_vals = {}
            for idx, (_, name) in enumerate(func_signature.arguments):
                if idx > 0 and input_str.startswith(","):
                    input_str = input_str[1:].strip()
                if idx == 0:
                    if input_str.startswith(f"{name} = "):
                        input_str = input_str[len(f"{name} = "):].strip()
                else:
                    assert input_str.startswith(f"{name} = ")
                    input_str = input_str[len(f"{name} = "):].strip()
                input_val, input_str = parse_value(input_str)
                input_vals[name] = input_val
            assert len(input_str) == 0

            output_val, output_str = parse_value(output_str)
            assert len(output_str) == 0

            examples.append(Example(input_vals, output_val))

        return ProblemSignature(func_signature, examples)


def generate_code(problem: Problem, signature: Union[ProblemSignature, InteractiveProblemSignature]) -> Tuple[str, str]:
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
                            decl_assign(func_sig.return_type, ret_name, f"{instance_name}.{call(ex.function, args)}"),
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


def create_project(project_name: str, problems: List[Problem]) -> None:
    if not os.path.exists(project_name):
        os.mkdir(project_name)
    with open("template.cpp", "r") as f:
        template = f.read().strip().split("\n")
    solution_start_line = template.index("// BEGIN SOLUTION CLASS")
    solution_end_line = template.index("// END SOLUTION CLASS")
    test_start_line = template.index("// BEGIN TEST")
    test_end_line = template.index("// END TEST")

    file_names = [chr(ord('A') + idx) for idx in range(len(problems))]
    for idx, problem in enumerate(problems):
        problem_signature = parse_problem(problem)
        solution_code, test_code = generate_code(problem, problem_signature)
        lines = "\n".join([
            "\n".join(template[:(solution_start_line + 1)]),
            solution_code,
            "\n".join(template[solution_end_line:(test_start_line + 1)]),
            test_code,
            "\n".join(template[test_end_line:])])
        with open(os.path.join(project_name, f"{file_names[idx]}.cpp"), "w") as f:
            f.write(lines + "\n")

    shutil.copy("testing.h", os.path.join(project_name, "testing.h"))

    cmake = [
        "cmake_minimum_required(VERSION 3.12)",
        "project(leetcode)",
        "set(CMAKE_CXX_STANDARD 17)",
        'set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DLEETCODE_LOCAL")',
        *[f"add_executable({name} {name}.cpp)" for name in file_names],
    ]
    with open(os.path.join(project_name, "CMakeLists.txt"), "w") as f:
        f.write("\n".join(cmake))


def main():
    # username = sys.argv[1]
    # password = getpass.getpass()
    #
    # try:
    #     print(f"Updating cookie for account `{username}`")
    #     update_cookie(username, password)
    # except WebDriverException as e:
    #     traceback.print_exc()
    #     print(e.__class__.__name__ + ': ' + str(e))

    contest_name = "weekly-contest-163"
    cache_file = f"{contest_name}.pkl"
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            problems = pickle.load(f)
    else:
        problems = get_problems(f"https://leetcode.com/contest/{contest_name}")
        # Save the raw info just in case.
        with open(cache_file, "wb") as f:
            pickle.dump(problems, f)

    create_project(contest_name, problems)


if __name__ == '__main__':
    main()
