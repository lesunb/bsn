CMAKE_MINIMUM_REQUIRED(VERSION 2.8.3)
PROJECT(component)

add_compile_options(-std=c++11)

## Find catkin and any catkin packages
FIND_PACKAGE(catkin REQUIRED COMPONENTS
  roscpp
  std_msgs
  genmsg
  messages
  archlib
  lepton
  libbsn
)

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

# Add executables for G3T1 series (g3t1_1, g3t1_2, etc.)
SET(g3t1_1-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g3t1_1/G3T1_1.cpp")
ADD_EXECUTABLE(g3t1_1 "${CMAKE_CURRENT_SOURCE_DIR}/apps/g3t1_1.cpp" ${${PROJECT_NAME}-src} ${g3t1_1-src})
TARGET_LINK_LIBRARIES(g3t1_1 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g3t1_1 messages_generate_messages_cpp)

SET(g3t1_2-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g3t1_2/G3T1_2.cpp")
ADD_EXECUTABLE(g3t1_2 "${CMAKE_CURRENT_SOURCE_DIR}/apps/g3t1_2.cpp" ${${PROJECT_NAME}-src} ${g3t1_2-src})
TARGET_LINK_LIBRARIES(g3t1_2 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g3t1_2 messages_generate_messages_cpp)

SET(g3t1_3-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g3t1_3/G3T1_3.cpp")
ADD_EXECUTABLE(g3t1_3 "${CMAKE_CURRENT_SOURCE_DIR}/apps/g3t1_3.cpp" ${${PROJECT_NAME}-src} ${g3t1_3-src})
TARGET_LINK_LIBRARIES(g3t1_3 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g3t1_3 messages_generate_messages_cpp)

SET(g3t1_4-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g3t1_4/G3T1_4.cpp")
ADD_EXECUTABLE(g3t1_4 "${CMAKE_CURRENT_SOURCE_DIR}/apps/g3t1_4.cpp" ${${PROJECT_NAME}-src} ${g3t1_4-src})
TARGET_LINK_LIBRARIES(g3t1_4 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g3t1_4 messages_generate_messages_cpp)

SET(g3t1_5-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g3t1_5/G3T1_5.cpp")
ADD_EXECUTABLE(g3t1_5 "${CMAKE_CURRENT_SOURCE_DIR}/apps/g3t1_5.cpp" ${${PROJECT_NAME}-src} ${g3t1_5-src})
TARGET_LINK_LIBRARIES(g3t1_5 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g3t1_5 messages_generate_messages_cpp)

SET(g3t1_6-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g3t1_6/G3T1_6.cpp")
ADD_EXECUTABLE(g3t1_6 "${CMAKE_CURRENT_SOURCE_DIR}/apps/g3t1_6.cpp" ${${PROJECT_NAME}-src} ${g3t1_6-src})
TARGET_LINK_LIBRARIES(g3t1_6 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g3t1_6 messages_generate_messages_cpp)

SET(g4t1-src "${CMAKE_CURRENT_SOURCE_DIR}/src/g4t1/G4T1.cpp")
ADD_EXECUTABLE(g4t1 "${CMAKE_CURRENT_SOURCE_DIR}/apps/g4t1.cpp" ${${PROJECT_NAME}-src} ${g4t1-src})
TARGET_LINK_LIBRARIES(g4t1 ${catkin_LIBRARIES} ${LIBRARIES})
ADD_DEPENDENCIES(g4t1 messages_generate_messages_cpp)

SET(patient_data_service-test "${CMAKE_CURRENT_SOURCE_DIR}/test/patient_data_service.cpp")
add_executable(patient_data_service "${CMAKE_CURRENT_SOURCE_DIR}/test/patient_data_service.cpp" ${${PROJECT_NAME}-test} ${patient_data_service-test})
target_link_libraries(patient_data_service
  ${catkin_LIBRARIES}
  ${LIBRARIES}
)
ADD_DEPENDENCIES(patient_data_service messages_generate_messages_cpp)

# Adicionar flags de cobertura SOMENTE se estivermos em modo Debug
if(CMAKE_BUILD_TYPE MATCHES Debug)
    message(STATUS "Build de Debug detectado: Habilitando Cobertura de Código (GCOV)")
    
    # -O0: Desativa otimizações (essencial para que a linha do código bata com a execução)
    # -fprofile-arcs: Instrumenta o código para contar execuções
    # -ftest-coverage: Gera dados para o GCOV
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-arcs -ftest-coverage -O0")
    
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fprofile-arcs -ftest-coverage")
endif()

if (CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  find_package(ros_pytest REQUIRED)
  add_rostest(test/test_bdd/test_target_system.launch)
  add_rostest(test/test_bdd/test_health_status.launch)
  add_rostest(test/test_bdd/test_data_persistance.launch)
  add_rostest(test/test_bdd/test_knowledge_repo.launch)
  add_rostest(test/test_bdd/test_managing_system.launch)
  add_rostest(test/test_bdd/test_injector.launch)
  add_rostest(test/test_bdd/test_check_bsn.launch)
  
  # unit test
  add_rostest(test/unit/test_G3T1_1.launch)
  add_rostest(test/unit/test_G3T1_2.launch)
  add_rostest(test/unit/test_G3T1_3.launch)
  add_rostest(test/unit/test_G3T1_4.launch)
  add_rostest(test/unit/test_G3T1_5.launch)
  add_rostest(test/unit/test_G3T1_6.launch)

  add_rostest(test/unit/test_G3T1_1_connected.launch)
  add_rostest(test/unit/test_G3T1_2_connected.launch)
  add_rostest(test/unit/test_G3T1_3_connected.launch)
  add_rostest(test/unit/test_G3T1_4_connected.launch)
  add_rostest(test/unit/test_G3T1_5_connected.launch)
  add_rostest(test/unit/test_G3T1_6_connected.launch)
  
  add_rostest(test/unit/test_G4T1.launch)
endif()


#if(CATKIN_ENABLE_TESTING)
#    catkin_add_nosetests(test/integration/test_my_cpp_node.py)
#    catkin_add_nosetests(test/bdd/behave_config.py)
#endif()

###########################################################################
# Install this project (if needed)
#INSTALL(TARGETS ${PROJECT_NAME}
#    ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
#    LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
#    RUNTIME DESTINATION ${CATKIN_GLOBAL_BIN_DESTINATION})

#INSTALL(DIRECTORY include/${PROJECT_NAME}/
#        DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION})

