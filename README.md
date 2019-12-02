# LeetCode Contest Helper

> A LeetCode contest utility for the dead serious.


## A Bit of Background...

If you've taken part in [LeetCode contests](https://leetcode.com/contest/), you might have been annoyed by their
ridiculous sample input formats. I know I have. The format of LeetCode format is similar to that of TopCoder -- you're
required to implement a specific function in a "Solution" class, and input is provided as arguments, while output is the
return value. While this alleviates the burden of hand-written I/O, it makes local testing especially difficult.

TopCoder contestants might be familiar with Arena plug-ins like
[TZTester](https://community.topcoder.com/contest/classes/TZTester/TZTester.html), which parses test cases and
generates a template code file that runs your solution against the test cases locally. Well, that's what this project
aims to do.


## Usage

1. Install [Selenium](https://selenium-python.readthedocs.io/installation.html) and the
   [Chrome web driver](https://sites.google.com/a/chromium.org/chromedriver/downloads) by following instructions
   in the links.

   **Note:** Although not tested, the code should also work with other web drivers supported by Selenium. Please change
   the code accordingly if you wish to use alternative browsers.
2. Clone the repository:
   ```bash
   git clone https://github.com/huzecong/leetcode-contest-helper.git
   cd leetcode-contest-helper
   ```
3. Login using your LeetCode account:
   ```bash
   python main.py login <username>
   ```
   A browser window will open and navigate to the LeetCode login page. Please enter your credentials and click login
   (and get pass CAPTCHAs if they pop up).

   If your account is registered on [LeetCode-CN](https://leetcode-cn.com), use this command instead:
   ```bash
   python main.py login -s leetcode-cn <username>
   ```

   **Note:** Unfortunately, it is not possible to access problem statements without logging in, as LeetCode prevents you
   from accessing the problems unless you have taken part in the contest or have a premium subscription. LCHelper stores
   your cookies and uses them to access the problems. Don't worry, your sensitive information is always stored locally.

   **Note:** Third-party login is not supported as of now.
4. Download problem descriptions and generate testing code in your favorite language:
   ```bash
   python main.py get [-l <language>] <url-to-contest-page>
   ```
   For instance, to generate testing code in C++ and Python (not supported yet) for
   [Weekly Contest 163](https://leetcode.com/contest/weekly-contest-163), run the command:
   ```bash
   python main.py get -l cpp -l python -o projects/ https://leetcode.com/contest/weekly-contest-163
   ```
   This will generate two folders under the folder `projects/`:

   - `weekly-contest-163_cpp`: C++ code of problems in the contest.
   - `weekly-contest-163_python`: Python code of problems in the contest.


## Language-specific Instructions

Currently, only C++ is supported, but Python support is planned.

### C++

The generated C++ project builds using CMake. To setup the build system, run the following commands:
```bash
cmake .
make
./A  # to run tests for problem A
```
You can also use IDEs (e.g., JetBrains CLion) to automate the process.
 
Note that problems are renamed to single uppercase letters (in the same order as on the web page) for simplicity.

The generated code contains quite a lot of boilerplate code for debugging. When submitting, remember to copy everything
between the lines `// BEGIN SUBMIT` and `// END SUBMIT`.

You can use your own template by modifying the `TEMPLATE_CODE` class variable in the file `lchelper/codegen/cpp.py`, but
you should only do so if you understand what you're doing. Remember to keep the following parts intact:

- Comments `// BEGIN *` and `// END *`. The code generator needs them to know where to insert generated code.
- `struct TreeNode`, `const int NONE`, and `TreeNode *_construct_tree()`. These are required to handle tree inputs in
  LeetCode format.
- `#include "testing.h"`. This include points to a tiny header-only library for testing your output.


## TODO

- [ ] Python code generation
- [ ] Automatic submission 
- [ ] Customized code templates
- [ ] Third-party login
