cmake_minimum_required(VERSION 3.8)
project(footbot_gazebo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ignition-gazebo6 REQUIRED)

add_library(footbot_ball_drag_system SHARED
  src/BallDragSystem.cc
)
target_link_libraries(footbot_ball_drag_system
  ignition-gazebo6::ignition-gazebo6
)

install(
  DIRECTORY worlds models config
  DESTINATION share/${PROJECT_NAME}
)

install(
  TARGETS footbot_ball_drag_system
  LIBRARY DESTINATION lib
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  # uncrustify mis-detects Gazebo system plugin .cc files as C in this setup
  set(ament_cmake_uncrustify_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
