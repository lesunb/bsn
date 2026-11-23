CMAKE_MINIMUM_REQUIRED (VERSION 2.8.3)
PROJECT(logging_infrastructure)

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

SET(logger-src "${CMAKE_CURRENT_SOURCE_DIR}/src/Logger.cpp")
ADD_EXECUTABLE (logger  "${CMAKE_CURRENT_SOURCE_DIR}/apps/logger.cpp" ${${PROJECT_NAME}-src} ${logger-src})
TARGET_LINK_LIBRARIES (logger ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(logger messages_generate_messages_cpp)

###########################################################################
# Tests.
if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  find_package(ros_pytest REQUIRED)

  add_rostest(test/unit/test_logger.launch)
endif()