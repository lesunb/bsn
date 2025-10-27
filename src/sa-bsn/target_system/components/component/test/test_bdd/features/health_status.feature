Feature: Patient Health Status (BSN-P10) - Whether the bodyhub has processed some data, it eventually will detect a new patient health status.

	Scenario: Successful Health Status (Happy Path)
		Given that nodes thermometer and central hub are online
		When I listen to thermometer
		Then g4t1 will detect new patient health status

	Scenario: Failure to Detect Health Status (Sad Path)
		Given that nodes thermometer and central hub are online
		When an internal processing error occurs in g4t1
		And I listen to thermometer
		Then Central hub will fail to detect the new patient health status