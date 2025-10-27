Feature: Data Persistence (BSN-P08) - Whether the sensor node has collected some data, eventually the bodyhub will persist it.

	Scenario: Data Persisted Successfully (Happy Path)
		Given that persistence system is online
		When I listen to thermometer
		And I send data to collector
		Then the data will be in persist topic
		
	Scenario: Data Not Persisted (Sad Path)
		Given that persistence system is online
		When I listen to thermometer
		And I send data to collector
		But a database error prevents persistence
		Then the system must log a persistence failure
