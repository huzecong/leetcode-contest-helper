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
   For instance, to generate testing code in C++ and Python for
   [Weekly Contest 163](https://leetcode.com/contest/weekly-contest-163), run the command:
   ```bash
   python main.py get -l cpp -l python -o projects/ https://leetcode.com/contest/weekly-contest-163
   ```
   This will generate two folders under the folder `projects/`:

   - `weekly-contest-163_cpp`: C++ code of problems in the contest.
   - `weekly-contest-163_python`: Python code of problems in the contest.


## Instructions for Using Generated Code

The project folder will contain one code file for each problem, and potentially other files required for compiling or
testing. Problems are renamed to single uppercase letters (in the same order as on the web page) for simplicity.

The generated code contains a certain amount of boilerplate code for debugging. When submitting, remember to copy
everything between the comments `BEGIN SUBMIT` and `END SUBMIT`.

You can add your custom code template to the generated code. Currently, this is only possible through modifying the code
for LCHelper:

1. Find the code generator class for your language. The C++ generator is located in `lchelper/codegen/cpp.py`, and the
   Python generator in `lchelper/codegen/python.py`.
2. Add a property named `user_template_code`, and make it return you code template. The syntax looks like this:
   ```python
   @property
   def user_template_code(self) -> str:
       return r"""
   template <typename ...Args>
   void my_amazing_debug_function(Args ...args) {
       // ...
   }
   """
   ```
   The property might already exist (it does in C++), in this case, feel free to replace it with your own.

See below for language-specific instructions. Currently, only C++ and Python are supported.

### C++

The C++ project folder contains these additional files:

- `CMakeLists.txt`, CMake configuration for building the project.
- `_testing.h`, a header-only library for comparing outputs.
- `_boilerplate.h`, boilerplate code for LeetCode-specific stuff.

The generated C++ project builds using CMake. To compile the problems, run the following commands:
```bash
cmake .
make
./A  # to run tests for problem A
```
You can also use IDEs (e.g., JetBrains CLion) to automate the process.


## Disclaimer

- This tool is not affiliated, associated, authorized, endorsed by, or in any way officially connected with LeetCode.
- This tool is not guaranteed to generate correct code, although the author tried their best to prevent such cases.
- This tool is not (and will not be) capable of automatically generating solutions.
- This tool does not grant you access to premium LeetCode problems that you cannot view with your personal account.
- Passing test cases within the generated code does not guarantee the correctness of your solution.


## TODO

- [ ] Automatic submission 
- [ ] Third-party login
- [ ] Interactive problems with a query class
