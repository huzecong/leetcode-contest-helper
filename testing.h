#ifndef TESTING_H
#define TESTING_H

#include <iostream>
#include <vector>

template <typename T>
void print(const T &x) { std::cout << x; }

template <typename T>
void print(const std::vector<T> &vec) {
    for (int i = 0; i < vec.size(); ++i) {
        std::cout << (i == 0 ? "{" : ", ");
        print(vec[i]);
    }
    std::cout << "}";
}

template <>
void print(const bool &x) { std::cout << (x ? "true" : "false"); }

template <typename T>
inline bool _test(const T &a, const T &b) {
    return a == b;
}

template <typename T>
inline bool _test(const std::vector<T> &a, const std::vector<T> &b) {
    if (a.size() != b.size()) return false;
    for (int i = 0; i < a.size(); ++i)
        if (!_test(a[i], b[i])) return false;
    return true;
}

template <typename T>
inline void test(const char *msg, const T &a, const T &b) {
    if (_test(a, b)) {
        std::cout << msg << " [OK]" << std::endl;
    } else {
        std::cout << msg << " [WRONG]" << std::endl;
        std::cout << "Expected: ";
        print(a);
        std::cout << std::endl << "Received: ";
        print(b);
        std::cout << std::endl;
    }
}

#endif  // TESTING_H
