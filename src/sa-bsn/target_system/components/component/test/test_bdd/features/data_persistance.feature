Feature: Data Persistence (BSN-P08) - Whether the sensor node has collected some data, eventually the bodyhub will persist it.

	@behavior @bsn-p08 @persistence
	Scenario: A vital sign reading collected by a sensor is persisted in the knowledge repository (BSN-P08)
		Given the patient is being monitored by the thermometer
		When the thermometer reports a new vital sign reading
		Then that reading should be retrievable from the knowledge repository with the value reported

	@behavior @sad-path @bsn-p08 @persistence
	Scenario: A persistence failure is recorded when the knowledge repository cannot store a reading (BSN-P08)
		Given the knowledge repository is experiencing storage failures
		When the thermometer reports a new vital sign reading
		Then a persistence failure record identifying that reading should be available in the system log
