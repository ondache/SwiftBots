cmake_minimum_required(VERSION 3.15...3.26)

project(${SKBUILD_PROJECT_NAME} VERSION ${SKBUILD_PROJECT_VERSION} LANGUAGES C)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

Python_add_library(search_ext MODULE WITH_SOABI swiftbots/c_ext/search_ext.c)

install(TARGETS search_ext DESTINATION swiftbots/c_ext/)