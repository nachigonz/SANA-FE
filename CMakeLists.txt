cmake_minimum_required(VERSION 3.16)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

project(SANA-FE)

add_compile_options(
    -Wall -pedantic -Werror -g -fopenmp
)

file (GLOB SOURCE_FILES "*.cpp")
file (GLOB HEADER_FILES "*.hpp")

source_group(TREE ${CMAKE_CURRENT_SOURCE_DIR} FILES ${SOURCE_FILES} ${HEADER_FILES})

# Get the latest commit hash
execute_process(
    COMMAND git rev-parse HEAD
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    OUTPUT_VARIABLE GIT_COMMIT
    OUTPUT_STRIP_TRAILING_WHITESPACE)

add_compile_definitions(GIT_COMMIT="${GIT_COMMIT}")

include(FetchContent)
FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11
)

FetchContent_GetProperties(pybind11)
if(NOT pybind11_POPULATED)
    FetchContent_Populate(pybind11)
    add_subdirectory(${pybind11_SOURCE_DIR} ${pybind11_BINARY_DIR})
endif()
pybind11_add_module(simcpp 
	${SOURCE_FILES}
	${HEADER_FILES}
)

find_package(OpenMP REQUIRED)

add_executable(sim main.cpp)
target_sources(sim
    PRIVATE ${SOURCE_FILES}
	PRIVATE ${HEADER_FILES}
)

target_link_libraries(sim PRIVATE OpenMP::OpenMP_CXX)
