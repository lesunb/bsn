Feature: Check for bsn features

	Scenario: BSN-P12 If the BodyHub has processed data, it will eventually detect the patient's new health status.
		Given the Target System Data topic is online
		When I listen to topics:
			| Topic Name         |
			| thermometer data  |
			| ecg data          |
			| oximeter data     |
			| abps data         |
			| abpd data         |
			| glucosemeter data |
			| Target System Data  |
		Then sensors will process the risks
		And Target System Data will receive the risks from sensors and detect patient's status

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
