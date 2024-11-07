Feature: Check for bsn features

	@happy_path
	Scenario: BSN-P11 If data has been sent by the sensor node, the BodyHub is able to process it as low, moderate or high risk vital sign data.
		Given the Target System Data topic is online
		When I listen to topics:
			| Topic Name        |
			| thermometer data  |
			| ecg data          |
			| oximeter data     |
			| abps data         |
			| abpd data         |
			| glucosemeter data |
			| Target System Data|
		Then sensors will process the risks
		And Target System Data will receive the risks from sensors and detect patient's status
		
	@happy_path
	Scenario: BSN-P09 If data has been sent by the sensor node, the BodyHub is able to process it
		Given the Target System Data topic is online
		When I listen to topics:
			| Topic Name        |
			| thermometer data  |
			| ecg data          |
			| oximeter data     |
			| abps data         |
			| abpd data         |
			| glucosemeter data |
			| Target System Data|
		Then sensors will process the data
		And Target System Data will receive the data from sensors

	@inactive_central_hub
	Scenario: BSN-P11 - Sad Path: central hub is inactive
		Given the Target System Data topic is online
		And the node g4t1 is inactive
		When I listen to topics:
			| Topic Name           |
			| thermometer data      |
			| ecg data              |
			| Target System Data     |
		Then sensors will process the risks
		And Target System Data should not receive any risk data or detect patient's status

	@inactive_central_hub
	Scenario: BSN-P09 - Sad Path: central hub is inactive
		Given the Target System Data topic is online
		And the node g4t1 is inactive
		When I listen to topics:
			| Topic Name            |
			| thermometer data      |
			| ecg data              |
			| Target System Data    |
		Then sensors will process the risks
		And Target System Data should not receive any risk data or detect patient's status