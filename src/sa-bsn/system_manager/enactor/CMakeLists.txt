CMAKE_MINIMUM_REQUIRED (VERSION 2.8.3)
PROJECT(enactor)

add_compile_options(-std=c++11)

###########################################################################
## Find catkin and any catkin packages
FIND_PACKAGE(catkin REQUIRED COMPONENTS roscpp std_msgs genmsg roslib messages archlib libbsn)

###########################################################################
# Export catkin package.
CATKIN_PACKAGE(
    INCLUDE_DIRS include
    LIBRARIES ${PROJECT_NAME}
    CATKIN_DEPENDS messages message_runtime archlib libbsn
)

###########################################################################
# Set catkin directory.
INCLUDE_DIRECTORIES(${catkin_INCLUDE_DIRS})

# Set include directory.
INCLUDE_DIRECTORIES(include)

###########################################################################
# Build this project.
FILE(GLOB ${PROJECT_NAME}-src "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")

SET(enactor-src "${CMAKE_CURRENT_SOURCE_DIR}/src/Controller.cpp")
ADD_EXECUTABLE (enactor "${CMAKE_CURRENT_SOURCE_DIR}/apps/controller.cpp" ${${PROJECT_NAME}-src} ${enactor-src} ${CMAKE_CURRENT_SOURCE_DIR}/src/Enactor.cpp)
TARGET_LINK_LIBRARIES (enactor ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(enactor messages_generate_messages_cpp)

###########################################################################
# Tests.
if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  find_package(ros_pytest REQUIRED)

  # Both launches bring up a real `data_access` (repository package) node
  # alongside enactor - see test/unit/test_enactor.py's module docstring for
  # why. They are split because `adaptation_parameter` is read once, in
  # Controller::setUp(), and selects which half of Controller.cpp runs:
  # test_enactor.launch covers the cost path, test_enactor_reliability.launch
  # the reliability one (the path the deployed system uses).
  add_rostest(test/unit/test_enactor.launch)
  add_rostest(test/unit/test_enactor_reliability.launch)
endif()