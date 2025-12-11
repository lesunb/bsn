Feature: Check for bsn features

	# @full_system
	Scenario: BSN-P09 If data has been sent by the sensor node, the BodyHub is able to process it as low, moderate or high risk vital sign data.
		# Scenario: sucessful process
		Given that all sensors and central hub nodes are online
		When I listen to sensors data
		Then sensors will process the risks
		And Central hub will process the risk

	# @full_system
	Scenario: BSN-P08 If data has been sent by the sensor node, the BodyHub is able to process it
		# Scenario: sucessful process
		Given that all sensors and central hub nodes are online
		When I listen to sensors data
		Then Sensors will process the data
		And Central hub will receive data from sensors

	# @inactive_central_hub
	Scenario: BSN-P09 - Sad Path: central hub is inactive
		# Scenario: central hub is inactive (Sad Path)
		Given that all sensors are and online Central hub is inactive
		And Central hub is inactive
		When I listen to ecg and thermometer data
		Then sensors will process the risks
		But Central hub will not process the risk
		
	# @inactive_central_hub
	Scenario: BSN-P08 - Sad Path: central hub is inactive
		# Scenario: central hub is inactive (Sad Path)
		Given that all sensors are and online Central hub is inactive
		When I listen to ecg and thermometer data
		Then Sensors will process the data
		# not process data
		But Central hub will not process the data
