import argparse
import os
import pickle
import sys
from typing import Any, Dict, List, Optional, NoReturn

import lchelper

PROGRAM = "python main.py"
CACHE_FILE = "contest_problems.pkl"


def parse_args():
    class CustomParser(argparse.ArgumentParser):
        def error(self, message: str) -> NoReturn:
            self.print_help(sys.stderr)
            sys.stderr.write("\nerror: " + message + "\n")
            sys.exit(2)

    parser = CustomParser()
    subparsers = parser.add_subparsers(dest="command")

    parser_login = subparsers.add_parser("login", help="Log in using your LeetCode account")
    parser_login.add_argument("username", help="Your LeetCode account username")

    parser_get = subparsers.add_parser("get", help="Download contest problems and generate testing code")
    parser_get.add_argument("-u", "--username", dest="username", default=None,
                            help="The LeetCode account to use, required if you logged in with multiple accounts")
    parser_get.add_argument("-l", "--lang", metavar="LANG", dest="lang", nargs="+", required=True,
                            choices=list(lchelper.LANGUAGES.keys()),
                            help="Languages to generate testing code for, supported languages are: [%(choices)s]")
    parser_get.add_argument("--no-cache", action="store_true", default=False,
                            help="Do not use cached problem descriptions when generating code")
    parser_get.add_argument("-o", "--output", dest="output", default="./",
                            help="The path to store generated projects")
    parser_get.add_argument("url", help="URL to the contest page")

    args = parser.parse_args()
    if not args.command:
        parser.print_help(sys.stderr)
    return args


def main():
    args = parse_args()

    if args.command == "login":
        print(f"Logging in using account '{args.username}'. Please enter your password in the browser window.")
        lchelper.update_cookie(args.username)
        print(f"Cookies for user '{args.username}' saved.")

    elif args.command == "get":
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "rb") as f:
                info = pickle.load(f)
        else:
            info = {}

        cached_problems: Optional[List[Dict[str, Any]]] = None
        if not args.no_cache:
            if args.url in info:
                cached_problems = info[args.url]

        if cached_problems is None:
            available_users = lchelper.get_users()
            if len(available_users) == 0:
                print(f"You're not logged in. Please run `{PROGRAM} login <username>` first.")
                exit(1)
            if args.username is None and len(available_users) > 1:
                print(f"You have logged in with multiple accounts: {', '.join(repr(s) for s in available_users)}.\n"
                      f"Please select the user using the `-u <username>` flag.")
                exit(1)
            if args.username is not None and args.username not in available_users:
                print(f"The specified user '{args.username}' is not logged in.\n"
                      f"Please log in by running `{PROGRAM} login {args.username}` first.")
                exit(1)

            username = args.username if args.username is not None else available_users[0]
            problems = lchelper.get_problems(args.url, username)

            info[args.url] = [lchelper.to_dict(p) for p in problems]
            with open(CACHE_FILE, "wb") as f:
                pickle.dump(info, f)
        else:
            problems = [lchelper.from_dict(lchelper.Problem, p) for p in cached_problems]

        contest_name = args.url.rstrip('/').split('/')[-1]  # use the final URL segment as contest nme
        for lang in args.lang:
            codegen_class = lchelper.LANGUAGES[lang]
            project_path = os.path.join(args.output, f"{contest_name}_{lang}")
            codegen_class.create_project(project_path, problems)
            lchelper.log(f"Project in language '{lang}' stored at: {project_path}", "success")


if __name__ == '__main__':
    main()
