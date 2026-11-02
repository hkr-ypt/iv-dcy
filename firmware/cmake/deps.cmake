# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lucas Wu
#
# Third-party sources, fetched at configure time at pinned releases.  Each is
# a shallow clone of a release tag, then checked against the expected commit
# so that a moved tag cannot silently change the build.
#
# Offline builds: point FETCHCONTENT_SOURCE_DIR_<NAME> at an existing checkout,
# e.g. -DFETCHCONTENT_SOURCE_DIR_TINYUSB=/path/to/tinyusb
#
#   name             licence      used for
#   tinyusb          MIT          USB device stack (CDC-ACM, STM32 fsdev driver)
#   cmsis_device_f0  Apache-2.0   STM32F0 register definitions
#   cmsis_core       Apache-2.0   Cortex-M0 core header (CMSIS 6)
include(FetchContent)

function(iv_dcy_dependency name repository tag commit)
    FetchContent_Declare(${name}
        GIT_REPOSITORY ${repository}
        GIT_TAG ${tag}
        GIT_SHALLOW TRUE
        GIT_PROGRESS FALSE
        SOURCE_SUBDIR do-not-add-subdirectory)
    FetchContent_MakeAvailable(${name})
    set(dir "${${name}_SOURCE_DIR}")
    string(TOUPPER "${name}" upper)
    if(FETCHCONTENT_SOURCE_DIR_${upper})
        message(STATUS "${name}: using ${dir} (commit not checked)")
    else()
        execute_process(COMMAND git -C "${dir}" rev-parse HEAD
                        OUTPUT_VARIABLE got OUTPUT_STRIP_TRAILING_WHITESPACE)
        if(NOT got STREQUAL commit)
            message(FATAL_ERROR "${name} ${tag}: expected commit ${commit}, got '${got}'")
        endif()
        message(STATUS "${name} ${tag} (${commit})")
    endif()
    set(${name}_SOURCE_DIR "${dir}" PARENT_SCOPE)
endfunction()

macro(iv_dcy_fetch_tinyusb)
    iv_dcy_dependency(tinyusb https://github.com/hathach/tinyusb.git
                      0.21.0 dae3f9a366bfcddbf9dcf1b48d7500286a849539)
endmacro()

macro(iv_dcy_fetch_cmsis)
    iv_dcy_dependency(cmsis_device_f0 https://github.com/STMicroelectronics/cmsis-device-f0.git
                      v2.3.8 f6fbbfcdc80797779a7a1eec87f1002516ef0483)
    iv_dcy_dependency(cmsis_core https://github.com/ARM-software/CMSIS_6.git
                      v6.4.0 af1b110e46a1720349f6f125e386e126767699bd)
endmacro()
