Feature: Testing ROS1 nodes

	Scenario: Ensure the EffectorRegister service is available
		Given the ROS environment is working
		When I list the available ROS services
		Then the EffectorRegister service should be listed
