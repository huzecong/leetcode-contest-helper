import http.cookiejar
import os
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as Expected
from selenium.webdriver.support.wait import WebDriverWait

from lchelper.common import Problem
from lchelper.logging import log

__all__ = [
    "get_users",
    "update_cookie",
    "get_problems",
]

COOKIE_FOLDER = "cookies/"


def get_users() -> List[str]:
    r"""Return a list of users that we have cookies of."""
    if not os.path.exists(COOKIE_FOLDER):
        return []
    users = [file[:-len(".dat")] for file in os.listdir(COOKIE_FOLDER) if file.endswith(".dat")]
    return users


def update_cookie(username: str) -> None:
    r"""Update the cookie for the LeetCode user."""
    browser = webdriver.Chrome()
    browser.set_window_position(0, 0)
    browser.set_window_size(800, 600)
    browser.switch_to.window(browser.window_handles[0])
    browser.get('https://leetcode.com/accounts/login/')
    browser.implicitly_wait(10)

    WebDriverWait(browser, 123456789).until(
        Expected.visibility_of_element_located((By.CSS_SELECTOR, 'button[data-cy="sign-in-btn"]'))
    )

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

    WebDriverWait(browser, 123456789).until(
        Expected.presence_of_element_located((By.CSS_SELECTOR, 'img.avatar'))
    )

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
            rest={}
        ))
    browser.quit()

    if not os.path.exists(COOKIE_FOLDER):
        os.makedirs(COOKIE_FOLDER)
    cookie_path = os.path.join(COOKIE_FOLDER, f"{username}.dat")
    jar.save(cookie_path, ignore_discard=True, ignore_expires=True)


def get_problems(contest_url: str, username: str) -> List[Problem]:
    r"""Obtain the list of problems in a contest, given its URL.

    :param contest_url: URL to the contest page.
    :param username: Username of the user. Note that the user must be registered for the contest in order to see the
        problems during the contest.
    :return: A list of problem descriptions.
    """
    cookie_path = os.path.join(COOKIE_FOLDER, f"{username}.dat")
    if not os.path.exists(cookie_path):
        raise ValueError(f"No cookies found for user '{username}', please login first")

    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    browser = webdriver.Chrome(options=options)
    browser.set_window_position(0, 0)
    browser.set_window_size(800, 600)
    browser.implicitly_wait(10)

    log("Loading LeetCode contest page...")
    browser.get(contest_url)  # visit the page first to update the domain, and then set cookies
    cookie_jar = http.cookiejar.LWPCookieJar(cookie_path)
    cookie_jar.load(ignore_discard=True, ignore_expires=True)
    for c in cookie_jar:
        browser.add_cookie({"name": c.name, 'value': c.value, 'path': c.path, 'expiry': c.expires})

    elem = browser.find_element_by_css_selector("ul.contest-question-list")
    links = elem.find_elements_by_tag_name("a")
    problem_paths = [(link.get_attribute("href"), link.text) for link in links]
    log(f"Found problems: {[name for _, name in problem_paths]!r}")

    parsed_problems = []
    for idx, (problem_url, problem_name) in enumerate(problem_paths):
        browser.get(problem_url)
        statement = browser.find_element_by_css_selector("div.question-content").text
        examples = [
            elem.text for elem in browser.find_elements_by_css_selector("pre:not([class])") if elem.text]
        code = [elem.text for elem in browser.find_elements_by_css_selector("pre.CodeMirror-line")]
        problem = Problem(problem_url, problem_name, statement, examples, code)
        parsed_problems.append(problem)
        log(f"Parsed problem ({idx + 1}/{len(problem_paths)}): {problem_name}")

    browser.quit()
    log("All problems successfully parsed", "success")

    return parsed_problems
