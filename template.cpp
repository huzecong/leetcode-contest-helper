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

using namespace std;

#ifdef HZC

template <typename T>
void print(T *a, int n) {
    for (int i = 1; i < n; ++i)
        cerr << a[i] << " ";
    cerr << a[n] << endl;
}

#define PRINT(__l, __r, __s, __t) {                \
    cerr << #__l #__s << "~" << #__t #__r << ": "; \
    for (auto __i = __s; __i != __t; ++__i)        \
        cerr << __l __i __r << " ";                \
    cerr << endl;                                  \
}

template <typename T>
void print(const T &x) { cout << x; }

template <typename T>
void print(const vector<T> &vec) {
    for (int i = 0; i < vec.size(); ++i)
        cout << (i == 0 ? "{" : ", ") << vec[i];
    cout << "}";
}

template <>
void print(const bool &x) { cout << (x ? "true" : "false"); }

template <typename ...Args>
void debug(Args ...args);

template <>
void debug() { cout << endl; }

template <typename T, typename ...Args>
void debug(const T &x, Args ...args) {
    print(x);
    cout << " ";
    debug(args...);
}

#endif

// BEGIN SUBMIT

typedef long long ll;
typedef unsigned int uint;
template <class T>
using heap = priority_queue<T, vector<T>, greater<T>>;

inline double runtime() {
    return (double)clock() / CLOCKS_PER_SEC;
}

#ifndef HZC
# define print(...)
# define PRINT(...)
# define debug(...)
#endif

#define tget(a, b) get<b>(a)

struct TreeNode {
    int val;
    TreeNode *left;
    TreeNode *right;
    TreeNode(int x) : val(x), left(NULL), right(NULL) {}
};

// BEGIN SOLUTION CLASS

// END SOLUTION CLASS

// END SUBMIT

// BEGIN TEST

// END TEST
