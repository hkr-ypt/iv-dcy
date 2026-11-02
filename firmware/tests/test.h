/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 *
 * Minimal test helpers (no framework needed).
 */
#ifndef TEST_H
#define TEST_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int test_failures;

#define CHECK(cond)                                                          \
    do {                                                                     \
        if (!(cond)) {                                                       \
            fprintf(stderr, "%s:%d: CHECK failed: %s\n", __FILE__, __LINE__, \
                    #cond);                                                  \
            test_failures++;                                                 \
        }                                                                    \
    } while (0)

#define CHECK_STR(a, b)                                                      \
    do {                                                                     \
        const char *a_ = (a), *b_ = (b);                                     \
        if (strcmp(a_, b_) != 0) {                                           \
            fprintf(stderr, "%s:%d: expected \"%s\", got \"%s\"\n", __FILE__,\
                    __LINE__, b_, a_);                                       \
            test_failures++;                                                 \
        }                                                                    \
    } while (0)

#define TEST_RESULT()                                                        \
    (printf("%s: %s\n", __FILE__, test_failures ? "FAILED" : "passed"),      \
     test_failures ? EXIT_FAILURE : EXIT_SUCCESS)

#endif /* TEST_H */
