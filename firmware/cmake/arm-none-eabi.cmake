# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lucas Wu
#
# Toolchain file: GNU Arm Embedded (arm-none-eabi-gcc) for the Cortex-M0.
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)
set(CMAKE_OBJCOPY arm-none-eabi-objcopy CACHE FILEPATH "objcopy")
set(CMAKE_SIZE arm-none-eabi-size CACHE FILEPATH "size")

set(CMAKE_C_FLAGS_INIT "-mcpu=cortex-m0 -mthumb -ffunction-sections -fdata-sections")
set(CMAKE_EXE_LINKER_FLAGS_INIT
    "-mcpu=cortex-m0 -mthumb -nostartfiles -Wl,--gc-sections --specs=nano.specs --specs=nosys.specs")

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
