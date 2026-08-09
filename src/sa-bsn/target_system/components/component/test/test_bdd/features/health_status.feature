Feature: Patient Health Status (BSN-P10) - Whether the bodyhub has processed some data, it eventually will detect a new patient health status.

	# @behavior @bsn-p10  
	# Scenario: A patient health status is available after a sensor reports a reading (BSN-P10)  
	# 	Given the patient is being monitored by the thermometer  
	# 	When the thermometer reports a new vital sign reading
	# 	Then a patient health status derived from that reading should be available

	@behavior @sad-path @bsn-p10  
	Scenario: No patient health status is produced when the central hub cannot process a reading (BSN-P10)  
		Given the central hub is unable to process incoming readings  
		When the thermometer reports a new vital sign reading
		Then no new patient health status should be produced for that reading