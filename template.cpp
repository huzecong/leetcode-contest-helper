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

#include "testing.h"

using namespace std;

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

TreeNode *_construct_tree(const vector<int> &parent, int idx = 0) {
    if (idx >= parent.size() || parent[idx] == NONE) return NULL;
    TreeNode *root = new TreeNode(parent[idx]);
    root->left = _construct_tree(parent, idx * 2 + 1);
    root->right = _construct_tree(parent, idx * 2 + 2);
    return root;
}

// BEGIN SUBMIT

typedef long long ll;
typedef unsigned int uint;
template <class T>
using heap = priority_queue<T, vector<T>, greater<T>>;

inline double runtime() {
    return (double)clock() / CLOCKS_PER_SEC;
}

#ifndef LEETCODE_LOCAL
# define print(...)
# define PRINT(...)
# define debug(...)
#endif  // LEETCODE_LOCAL

#define tget(a, b) get<b>(a)

// BEGIN SOLUTION CLASS

// END SOLUTION CLASS

// END SUBMIT

// BEGIN TEST

// END TEST
