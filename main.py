import argparse
import os
import pickle
import sys
from typing import Any, Dict, List, Optional, NoReturn
from urllib.parse import urlparse

import lchelper
import lchelper.utils

PROGRAM = "python main.py"
CACHE_FILE = "contest_problems.pkl"


def parse_args():
    class CustomParser(argparse.ArgumentParser):
        def error(self, message: str) -> NoReturn:
            self.print_help(sys.stderr)
            sys.stderr.write("\nerror: " + message + "\n")
            sys.exit(2)

    parser = CustomParser()
    parser.add_argument("--debug", action="store_true", default=False)
    subparsers = parser.add_subparsers(dest="command")

    parser_login = subparsers.add_parser("login", help="Log in using your LeetCode account")
    parser_login.add_argument("username", help="Your LeetCode account username")
    parser_login.add_argument("-s", "--site", dest="site", choices=["leetcode", "leetcode-cn"], default="leetcode",
                              help="The LeetCode site for the account")

    parser_get = subparsers.add_parser("get", help="Download contest problems and generate testing code")
    parser_get.add_argument("-u", "--username", dest="username", default=None,
                            help="The LeetCode account to use, required if you logged in with multiple accounts")
    parser_get.add_argument("-l", "--lang", metavar="LANG", dest="lang", action="append", required=True,
                            choices=list(lchelper.LANGUAGES.keys()),
                            help="Languages to generate testing code for, supported languages are: [%(choices)s]")
    parser_get.add_argument("--no-cache", action="store_true", default=False,
                            help="Do not use cached problem descriptions when generating code")
    parser_get.add_argument("-o", "--output", dest="output", default="./",
                            help="The path to store generated projects")
    parser_get.add_argument("-p", "--prefix", dest="prefix", default=None,
                            help="Prefix for project folders, if not specified, the contest name (e.g. "
                                 "\"weekly-contest-162\") if used")
    parser_get.add_argument("url", help="URL to the contest page, or the contest name (e.g. \"weekly-contest-162\")")

    args = parser.parse_args()
    if not args.command:
        parser.print_help(sys.stderr)
    return args


def main():
    args = parse_args()
    if args.debug:
        lchelper.utils.register_excepthook()

    if args.command == "login":
        print(f"Logging in using account '{args.username}'. Please enter your password in the browser window.")
        lchelper.update_cookie(args.username, args.site)
        print(f"Cookies for user '{args.username}' saved.")

    elif args.command == "get":
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "rb") as f:
                info = pickle.load(f)
        else:
            info = {}

        url_parse = urlparse(args.url)
        if url_parse.netloc != "":  # URL instead of name
            contest_name = args.url.rstrip('/').split('/')[-1]  # use the final URL segment as contest nme
            site: Optional[str] = lchelper.utils.remove_affix(url_parse.netloc, "www.", ".com")
        else:
            contest_name = args.url
            site = None

        cached_problems: Optional[List[Dict[str, Any]]] = None
        if not args.no_cache:
            if (site, contest_name) in info:
                cached_problems = info[site, contest_name]

        if cached_problems is None:
            available_users = lchelper.get_users()
            if len(available_users) == 0:
                print(f"You're not logged in. Please run `{PROGRAM} login <username>` first.")
                exit(1)

            candidates = user_candidates = available_users
            if args.username is not None:
                candidates = user_candidates = [user for user in candidates if user.username == args.username]
            if site is not None:
                candidates = [user for user in candidates if user.site == site]
            # If there exist multiple candidates with different usernames, raise an error to avoid ambiguity.
            if len(set(user.username for user in candidates)) > 1:
                print(f"You have logged in with multiple accounts: {', '.join(repr(s) for s in candidates)}.\n"
                      f"Please select the user using the `-u <username>` flag.")
                exit(1)
            if len(candidates) == 0:
                if args.username is not None:
                    if len(user_candidates) > 0:
                        print(f"The specified user '{args.username}' is not from the site '{site}'.\n"
                              f"Please log in with a user from '{site}' by running "
                              f"`{PROGRAM} login -s {site} <username>`.")
                    else:
                        print(f"The specified user '{args.username}' is not logged in.\n"
                              f"Please log in by running `{PROGRAM} login {args.username}` first.")
                else:
                    print(f"There are no users from the site '{site}'.\n"
                          f"Please log in with a user from '{site}' by running `{PROGRAM} login -s {site} <username>`.")
                exit(1)

            user = candidates[0]
            cookie_path = lchelper.get_cookie_path(user.username, user.site)
            url = f"https://{user.site}.com/contest/{contest_name}"
            lchelper.log(f"User: {user}, URL: {url}")

            problems = lchelper.get_problems(url, user.site, cookie_path)

            info[site, contest_name] = [lchelper.utils.to_dict(p) for p in problems]
            with open(CACHE_FILE, "wb") as f:
                pickle.dump(info, f)
        else:
            problems = [lchelper.utils.from_dict(lchelper.Problem, p) for p in cached_problems]

        for lang in args.lang:
            codegen = lchelper.create_codegen(lang)
            project_path = os.path.join(args.output, f"{(args.prefix or contest_name)}_{lang}")
            codegen.create_project(project_path, problems, site, debug=args.debug)
            lchelper.log(f"Project in language '{lang}' stored at: {project_path}", "success")


if __name__ == '__main__':
    main()
