# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lucas Wu
#
# Host unit tests for the hardware-independent parts of the firmware.
#
#   cmake -S firmware/tests -B build/tests && cmake --build build/tests
#   ctest --test-dir build/tests --output-on-failure
cmake_minimum_required(VERSION 3.24)
project(iv_dcy_tests C)
set(CMAKE_C_STANDARD 11)

include(../cmake/deps.cmake)
iv_dcy_fetch_tinyusb()

set(SRC "${CMAKE_CURRENT_SOURCE_DIR}/../src")
set(WARN -Wall -Wextra -Werror)
option(IV_DCY_SANITIZE "build tests with ASan/UBSan" ON)
if(IV_DCY_SANITIZE)
    set(SAN -fsanitize=address,undefined -fno-sanitize-recover=all)
endif()

enable_testing()

add_executable(test_cli test_cli.c ${SRC}/cli.c)
target_include_directories(test_cli PRIVATE ${SRC})
target_compile_options(test_cli PRIVATE ${WARN} ${SAN})
target_link_options(test_cli PRIVATE ${SAN})
add_test(NAME cli COMMAND test_cli)

# The real usb_descriptors.c against TinyUSB's headers, with no MCU selected.
add_executable(test_descriptors test_descriptors.c ${SRC}/usb_descriptors.c)
target_include_directories(test_descriptors PRIVATE ${SRC})
target_include_directories(test_descriptors SYSTEM PRIVATE "${tinyusb_SOURCE_DIR}/src")
target_compile_definitions(test_descriptors PRIVATE CFG_TUSB_MCU=OPT_MCU_NONE TUP_DCD_ENDPOINT_MAX=8)
target_compile_options(test_descriptors PRIVATE ${WARN} ${SAN})
target_link_options(test_descriptors PRIVATE ${SAN})
add_test(NAME descriptors COMMAND test_descriptors)

add_test(NAME identity_single_source
         COMMAND ${CMAKE_COMMAND} -DSRC=${SRC} -P ${CMAKE_CURRENT_SOURCE_DIR}/check_identity.cmake)
