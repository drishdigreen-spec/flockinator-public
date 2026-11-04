cmake_minimum_required(VERSION 3.16)
project(flock_commissioning_crypto_tests LANGUAGES C CXX)
set(CMAKE_C_STANDARD 99)
set(CMAKE_CXX_STANDARD 17)
set(MBEDTLS_SOURCE_DIR "" CACHE PATH "Already-installed upstream Mbed TLS source directory")
if(NOT EXISTS "${MBEDTLS_SOURCE_DIR}/library/md.c")
    message(FATAL_ERROR "Set MBEDTLS_SOURCE_DIR to the existing ESP-IDF components/mbedtls/mbedtls directory")
endif()
add_library(portable_mbedtls STATIC
    "${MBEDTLS_SOURCE_DIR}/library/md.c"
    "${MBEDTLS_SOURCE_DIR}/library/sha256.c"
    "${MBEDTLS_SOURCE_DIR}/library/platform_util.c")
target_include_directories(portable_mbedtls PUBLIC
    "${MBEDTLS_SOURCE_DIR}/include" "${CMAKE_CURRENT_SOURCE_DIR}")
target_compile_definitions(portable_mbedtls PUBLIC MBEDTLS_CONFIG_FILE="host_mbedtls_config.h")
add_executable(test_crypto test_crypto.cpp)
target_compile_options(test_crypto PRIVATE -Wall -Wextra -Werror)
target_link_libraries(test_crypto PRIVATE portable_mbedtls)
enable_testing()
add_test(NAME production_crypto COMMAND test_crypto)
