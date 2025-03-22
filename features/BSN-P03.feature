Feature: BSN-P03: Whenever the patients' health status is on high risk and an emergency has been detected it implies that is less or equal 250 (ms)

	@reduced_system
	Scenario: Successful Sensor Execution
		Given that nodes thermometer and central hub are online
		When I listen to thermometer
		And thermometer sends data with high risk
		Then Central hub will detect an emergency in less than 250 ms

	@High_frequency_sensor_system
	Scenario: Overloaded sensor data
		Given that nodes thermometer and central hub are online
		When I listen to thermometer
		And themometer sends low-risk data with high frequency
		But thermometer sends data with high risk
		Then Central Hub will experience delayed emergency detection