CMAKE_MINIMUM_REQUIRED (VERSION 2.8.3)
PROJECT(effector)

add_compile_options(-std=c++11)

###########################################################################
## Find catkin and any catkin packages
FIND_PACKAGE(catkin REQUIRED COMPONENTS 
    roscpp 
    std_msgs 
    genmsg 
    messages 
    archlib 
    rospy
    std_srvs
    rostest
    )

###########################################################################
# Export catkin package.
CATKIN_PACKAGE(
    INCLUDE_DIRS include
    LIBRARIES ${PROJECT_NAME}
    CATKIN_DEPENDS messages message_runtime archlib
)

###########################################################################
# Set catkin directory.
INCLUDE_DIRECTORIES(${catkin_INCLUDE_DIRS})

# Set include directory.
INCLUDE_DIRECTORIES(include)

###########################################################################
# Build this project.
FILE(GLOB ${PROJECT_NAME}-src "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")

SET(param_adapter-src "${CMAKE_CURRENT_SOURCE_DIR}/src/ParamAdapter.cpp")
ADD_EXECUTABLE (param_adapter  "${CMAKE_CURRENT_SOURCE_DIR}/apps/param_adapter.cpp" ${${PROJECT_NAME}-src} ${param_adapter-src})
TARGET_LINK_LIBRARIES (param_adapter ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(param_adapter services_generate_messages_cpp)

###########################################################################
