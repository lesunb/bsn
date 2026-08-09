Feature: Check for bsn features

	@behavior @bsn-p08
	Scenario Outline: The central hub receives the vital sign reading reported by a body sensor (BSN-P08)
		Given the patient is being monitored by <sensor>
		When <sensor> reports a new vital sign reading
		Then the central hub should receive that reading with the value reported by <sensor>
		
		Examples:
			| sensor          |
			| the oximeter    |
			| the ECG sensor  |
			| the thermometer |
			| the SBP sensor  |
			| the DBP sensor  |
			| the glucometer  |
	
	
	@behavior @bsn-p08
	Scenario: The central hub classifies a vital sign reading outside the normal range as high risk (BSN-P08)
		Given the patient is being monitored by the oximeter
		When the oximeter reports a blood oxygenation reading outside its normal range
		Then the central hub should classify the patient risk for blood oxygenation as high

	@behavior @sad-path @bsn-p08
	Scenario: No patient risk level is reported while the central hub is unavailable (BSN-P08)
		Given the central hub is unavailable
		When the oximeter reports a new vital sign reading
		Then no patient risk level should be reported for that reading
