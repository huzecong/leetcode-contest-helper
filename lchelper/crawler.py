import http.cookiejar
import os
from typing import List

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as Expected
from selenium.webdriver.support.wait import WebDriverWait

from lchelper.common import Problem, User
from lchelper.logging import log

__all__ = [
    "get_users",
    "get_cookie_path",
    "update_cookie",
    "get_problems",
]

COOKIE_FOLDER = "cookies/"


def get_users() -> List[User]:
    r"""Return a list of users that we have cookies of."""
    if not os.path.exists(COOKIE_FOLDER):
        return []
    users = []
    for file in os.listdir(COOKIE_FOLDER):
        if file.endswith(".dat"):
            file = file[:-len(".dat")]
            *username, site = file.split("@")
            users.append(User('@'.join(username), site))
    return users


def get_cookie_path(username: str, site: str) -> str:
    if not os.path.exists(COOKIE_FOLDER):
        os.makedirs(COOKIE_FOLDER)
    return os.path.join(COOKIE_FOLDER, f"{username}@{site}.dat")


def check_login(browser, site: str, timeout: int = 10) -> bool:
    try:
        if site == "leetcode":
            WebDriverWait(browser, timeout).until(
                Expected.presence_of_element_located((By.CSS_SELECTOR, 'img.avatar')))
        else:  # site == "leetcode-cn"
            WebDriverWait(browser, timeout).until(
                Expected.presence_of_element_located((By.CSS_SELECTOR, 'span.ant-avatar')))
        return True
    except TimeoutException:
        return False


def update_cookie(username: str, site: str) -> None:
    r"""Update the cookie for the LeetCode user."""
    browser = webdriver.Chrome()
    browser.set_window_position(0, 0)
    browser.set_window_size(800, 600)
    browser.switch_to.window(browser.window_handles[0])
    url = f"https://{site}.com/accounts/login/"
    browser.get(url)
    browser.implicitly_wait(10)

    if site == "leetcode":
        WebDriverWait(browser, 10).until(
            Expected.visibility_of_element_located((By.CSS_SELECTOR, 'button[data-cy="sign-in-btn"]')))
    else:  # site == "leetcode-cn"
        WebDriverWait(browser, 10).until(
            Expected.visibility_of_element_located((By.CSS_SELECTOR, 'button[type="primary"]')))

    elem = browser.find_element_by_css_selector('input[name="login"]')
    elem.clear()
    elem.send_keys(username)

    # elem = browser.find_element_by_css_selector('input[type="password"]')
    # elem.clear()
    # elem.send_keys(password)
    #
    # print("User credentials filled")
    #
    # elem = browser.find_element_by_css_selector('button[data-cy="sign-in-btn"]')
    # browser.execute_script("arguments[0].click();", elem)

    if not check_login(browser, site, timeout=120):
        raise RuntimeError("Login failed!")

    cookies = browser.get_cookies()
    jar = http.cookiejar.LWPCookieJar()
    for cookie in cookies:
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
            rest={},
        ))
    browser.quit()

    cookie_path = get_cookie_path(username, site)
    jar.save(cookie_path, ignore_discard=True, ignore_expires=True)


def get_problems(contest_url: str, site: str, cookie_path: str) -> List[Problem]:
    r"""Obtain the list of problems in a contest, given its URL.

    :param contest_url: URL to the contest page.
    :param site: LeetCode site name.
    :param cookie_path: Path to the cookie to use for signing in.
    :return: A list of problem descriptions.
    """
    if not os.path.exists(cookie_path):
        raise ValueError(f"No cookies file found at path '{cookie_path}'. Please login first")

    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    browser = webdriver.Chrome(options=options)
    browser.set_window_position(0, 0)
    browser.set_window_size(3840, 600)  # a wide enough window so code does not get wrapped
    browser.implicitly_wait(10)

    log("Loading LeetCode contest page...")
    browser.get(contest_url)  # visit the page first to update the domain, and then set cookies
    cookie_jar = http.cookiejar.LWPCookieJar(cookie_path)
    cookie_jar.load(ignore_discard=True, ignore_expires=True)
    for c in cookie_jar:
        browser.add_cookie({"name": c.name, 'value': c.value, 'path': c.path})
    browser.get(contest_url)  # visit again to refresh page with cookies added

    if not check_login(browser, site, timeout=10):
        browser.quit()
        print(f"Cookie '{cookie_path}' might have expired. Please try logging in again")
        exit(1)

    elem = browser.find_element_by_css_selector("ul.contest-question-list")
    links = elem.find_elements_by_tag_name("a")
    problem_paths = [(link.get_attribute("href"), link.text) for link in links]
    log(f"Found problems: {[name for _, name in problem_paths]!r}")

    parsed_problems = []
    for idx, (problem_url, problem_name) in enumerate(problem_paths):
        browser.get(problem_url)
        try:
            # Page during contest; editor located below statement.
            statement_css_selector = "div.question-content"
            code_css_selector = "pre.CodeMirror-line"
            statement = browser.find_element_by_css_selector(statement_css_selector).text
        except (TimeoutException, NoSuchElementException):
            # Page after contest; statement and editor in vertically split panes.
            statement_css_selector = "div[data-key='description-content'] div.content__1Y2H"
            code_css_selector = "div.monaco-scrollable-element div.view-line"
            statement = browser.find_element_by_css_selector(statement_css_selector).text
        examples = [
            elem.text for elem in browser.find_elements_by_css_selector("pre:not([class])") if elem.text]
        # TODO: Should make sure C++ is selected!
        code = [elem.text for elem in browser.find_elements_by_css_selector(code_css_selector)]
        problem = Problem(problem_url, problem_name, statement, examples, code)
        parsed_problems.append(problem)
        log(f"Parsed problem ({idx + 1}/{len(problem_paths)}): {problem_name}")

    browser.quit()
    log("All problems successfully crawled", "success")

    return parsed_problems
