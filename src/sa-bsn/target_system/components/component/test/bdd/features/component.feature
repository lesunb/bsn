Feature: ROS Component Testing

	Scenario: Verify message publishing
		Given ROS is running
		When I publish a message to "/test_topic"
		Then the message should be received
