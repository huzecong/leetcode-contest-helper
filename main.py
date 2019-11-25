import getpass
import http.client
import http.cookiejar
import json
import os
import pickle
import socket
import sys
import tempfile
import traceback
from enum import Enum, auto

import requests
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.command import Command
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from typing import NamedTuple, List, Tuple, Dict, Any, Optional, Union


def save_screenshot_of(elem, browser):
    location = elem.location
    size = elem.size

    f = tempfile.NamedTemporaryFile()
    browser.save_screenshot(f.name)

    im = Image.open(f.name)
    left = location['x']
    top = location['y']
    right = left + size['width']
    bottom = top + size['height']
    im = im.crop((left, top, right, bottom))

    f.close()
    return im


def check_alive(browser):
    try:
        browser.execute(Command.STATUS)
        return True
    except (socket.error, http.client.CannotSendRequest, WebDriverException):
        return False


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


def generate_code(signature: ProblemSignature) -> Tuple[str, str]:
    r"""Generate code given the signature. Code consists of two parts:

    - Code for the solution class. This is basically the template as-is, but could also include the statement in
      comments.
    - Code for testing the solution. This includes test functions for each example, and also the main function where
      the test functions are called and results are compared.

    :return: A tuple of two strings, corresponding to code for the solution class, and code for testing.
    """


def create_project(project_name: str, problems: List[Problem]) -> None:
    if not os.path.exists(project_name):
        os.mkdir(project_name)
    for idx, problem in enumerate(problems):
        problem_signature = parse_problem(problem)
        solution_code, test_code = generate_code(problem_signature)
        with open(os.path.join(project_name, f"{idx}.cpp")) as f:
            f.write(template_code)


def main():
    username = sys.argv[1]
    password = getpass.getpass()

    try:
        print(f"Updating cookie for account `{username}`")
        update_cookie(username, password)
    except WebDriverException as e:
        traceback.print_exc()
        print(e.__class__.__name__ + ': ' + str(e))

    contest_name = "weekly-contest-163"
    problems = get_problems(f"https://leetcode.com/contest/{contest_name}")
    # Save the raw info just in case.
    with open(f"{contest_name}.pkl", "wb") as f:
        pickle.dump(problems, f)
    create_project(contest_name, problems)


if __name__ == '__main__':
    main()
