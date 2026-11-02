# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lucas Wu
#
# IV-DCY USB reference firmware for the STM32F042K6T6.
#
#   cmake -S firmware -B build/firmware
#   cmake --build build/firmware
#
# produces build/firmware/iv_dcy.{elf,bin,hex,map}.  Host unit tests are a
# separate project in tests/ (see firmware/README.md).
cmake_minimum_required(VERSION 3.24)

if(NOT CMAKE_TOOLCHAIN_FILE)
    set(CMAKE_TOOLCHAIN_FILE "${CMAKE_CURRENT_LIST_DIR}/cmake/arm-none-eabi.cmake")
endif()
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE MinSizeRel)
endif()

project(iv_dcy_firmware C)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_EXTENSIONS ON)   # GNU range designators in the vector table

include(cmake/deps.cmake)
iv_dcy_fetch_tinyusb()
iv_dcy_fetch_cmsis()

set(TUSB "${tinyusb_SOURCE_DIR}/src")
set(TINYUSB_SOURCES
    ${TUSB}/tusb.c
    ${TUSB}/common/tusb_fifo.c
    ${TUSB}/device/usbd.c
    ${TUSB}/class/cdc/cdc_device.c
    ${TUSB}/portable/st/stm32_fsdev/dcd_stm32_fsdev.c
    ${TUSB}/portable/st/stm32_fsdev/fsdev_common.c)

set(APP_SOURCES
    src/main.c
    src/board.c
    src/cli.c
    src/usb_descriptors.c
    src/startup_stm32f042.c)

add_executable(iv_dcy ${APP_SOURCES} ${TINYUSB_SOURCES})
set_target_properties(iv_dcy PROPERTIES SUFFIX ".elf")
target_include_directories(iv_dcy PRIVATE src ${TUSB})
target_include_directories(iv_dcy SYSTEM PRIVATE
    "${cmsis_device_f0_SOURCE_DIR}/Include"
    "${cmsis_core_SOURCE_DIR}/CMSIS/Core/Include")
target_compile_definitions(iv_dcy PRIVATE STM32F042x6)
target_compile_options(iv_dcy PRIVATE -g3)
# Our own sources build warning-free; third-party code keeps its own style.
set_source_files_properties(${APP_SOURCES} PROPERTIES COMPILE_OPTIONS
    "-Wall;-Wextra;-Wshadow;-Wstrict-prototypes;-Wmissing-prototypes;-Werror")
target_link_options(iv_dcy PRIVATE
    "-T${CMAKE_CURRENT_SOURCE_DIR}/src/stm32f042k6.ld"
    "-Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/iv_dcy.map"
    "-Wl,--print-memory-usage")

add_custom_command(TARGET iv_dcy POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:iv_dcy> iv_dcy.bin
    COMMAND ${CMAKE_OBJCOPY} -O ihex $<TARGET_FILE:iv_dcy> iv_dcy.hex
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE:iv_dcy>
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    COMMENT "iv_dcy.bin / iv_dcy.hex"
    VERBATIM)
