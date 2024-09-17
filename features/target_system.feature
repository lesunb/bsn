Feature: Ensure that central hub receives data from body sensors and publishes to data access node

	Scenario: Check if sensors are publishing data to /collector and to /g4t1
		Given the ROS environment is on
		When I check if the sensors are publishing data
		And I check if respective topics have data
		Then /g4t1 should receive data

	Scenario: Check if the central hub (/g4t1) is publishing to /data_access
		Given the ROS environment is on
		When the /g4t1 node is publishing data
		And respective topics have data
		Then the /data_access node should received it

	Scenario: Check if /param_adapter node communicate with the g3t1_n, g4t1 and /logger nodes
		Given the /param_adapter node is online
		When I check if topics /reconfigure are inbound from /logger
		And I check if topics /reconfigure_/g3t1_1 are outbound to /g3t1_1
		And I check if topics /reconfigure_/g3t1_2 are outbound to /g3t1_2
		And I check if topics /reconfigure_/g3t1_3 are outbound to /g3t1_3
		And I check if topics /reconfigure_/g3t1_4 are outbound to /g3t1_4
		And I check if topics /reconfigure_/g3t1_5 are outbound to /g3t1_5
		And I check if topics /reconfigure_/g3t1_6 are outbound to /g3t1_6
		And I check if topics /reconfigure_/g4t1 are outbound to /g4t1
		Then /param_adapter node is connected appropriately

	Scenario: Verify if rosservices in /Patient node transmit data
		Given the /Patient node is online
		When I call rosservice /getPatientData with oxigenation and None
		And I call rosservice /getPatientData with heart_rate and None
		And I call rosservice /getPatientData with abps and None
		And I call rosservice /getPatientData with abpd and None
		And I call rosservice /getPatientData with glucose and None
		Then response should not be null
