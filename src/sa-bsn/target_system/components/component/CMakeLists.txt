CMAKE_MINIMUM_REQUIRED (VERSION 2.8.3)
PROJECT(component)

add_compile_options(-std=c++11)

## Find catkin and any catkin packages
FIND_PACKAGE(catkin REQUIRED COMPONENTS roscpp std_msgs genmsg messages archlib lepton libbsn message_generation)

# Export catkin package.
CATKIN_PACKAGE(
    INCLUDE_DIRS include
    LIBRARIES ${PROJECT_NAME}
    CATKIN_DEPENDS messages message_runtime archlib lepton libbsn
)

###########################################################################
# Set catkin directory.
INCLUDE_DIRECTORIES(include ${catkin_INCLUDE_DIRS})

# Set include directory.
INCLUDE_DIRECTORIES(include)

###########################################################################
# Build this project.
FILE(GLOB ${PROJECT_NAME}-src "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")

SET(g3t1_1-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g3t1_1/G3T1_1.cpp")
ADD_EXECUTABLE (g3t1_1  "${CMAKE_CURRENT_SOURCE_DIR}/apps/g3t1_1.cpp" ${${PROJECT_NAME}-src} ${g3t1_1-src})
TARGET_LINK_LIBRARIES (g3t1_1 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g3t1_1 messages_generate_messages_cpp)

SET(g3t1_2-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g3t1_2/G3T1_2.cpp")
ADD_EXECUTABLE (g3t1_2  "${CMAKE_CURRENT_SOURCE_DIR}/apps/g3t1_2.cpp" ${${PROJECT_NAME}-src} ${g3t1_2-src})
TARGET_LINK_LIBRARIES (g3t1_2 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g3t1_2 messages_generate_messages_cpp)

SET(g3t1_3-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g3t1_3/G3T1_3.cpp")
ADD_EXECUTABLE (g3t1_3  "${CMAKE_CURRENT_SOURCE_DIR}/apps/g3t1_3.cpp" ${${PROJECT_NAME}-src} ${g3t1_3-src})
TARGET_LINK_LIBRARIES (g3t1_3 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g3t1_3 messages_generate_messages_cpp)

SET(g3t1_4-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g3t1_4/G3T1_4.cpp")
ADD_EXECUTABLE (g3t1_4  "${CMAKE_CURRENT_SOURCE_DIR}/apps/g3t1_4.cpp" ${${PROJECT_NAME}-src} ${g3t1_4-src})
TARGET_LINK_LIBRARIES (g3t1_4 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g3t1_4 messages_generate_messages_cpp)

SET(g3t1_5-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g3t1_5/G3T1_5.cpp")
ADD_EXECUTABLE (g3t1_5  "${CMAKE_CURRENT_SOURCE_DIR}/apps/g3t1_5.cpp" ${${PROJECT_NAME}-src} ${g3t1_5-src})
TARGET_LINK_LIBRARIES (g3t1_5 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g3t1_5 messages_generate_messages_cpp)

SET(g3t1_6-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g3t1_6/G3T1_6.cpp")
ADD_EXECUTABLE (g3t1_6  "${CMAKE_CURRENT_SOURCE_DIR}/apps/g3t1_6.cpp" ${${PROJECT_NAME}-src} ${g3t1_6-src})
TARGET_LINK_LIBRARIES (g3t1_6 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g3t1_6 messages_generate_messages_cpp)

SET(g4t1-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g4t1/G4T1.cpp")
ADD_EXECUTABLE (g4t1 "${CMAKE_CURRENT_SOURCE_DIR}/apps/g4t1.cpp" ${${PROJECT_NAME}-src} ${g4t1-src})
TARGET_LINK_LIBRARIES (g4t1 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g4t1 messages_generate_messages_cpp)


## Add folders to be run by python nosetests
# catkin_add_nosetests(test)

catkin_install_python(PROGRAMS src/covid_detection/covid_detection.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

#add_custom_target(
# run ALL
# COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/src/covid_detection/covid_detection.py &
#)

###########################################################################
# Install this project.
#INSTALL(TARGETS ${PROJECT_NAME}
#    ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
#    LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
#    RUNTIME DESTINATION ${CATKIN_GLOBAL_BIN_DESTINATION})

#INSTALL(DIRECTORY include/${PROJECT_NAME}/
#        DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION})
