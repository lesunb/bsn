Feature: ensure simulation components communicate properly

	# Scenario: Ensure the data is being injected into nodes /logger, /g3t1_6, /g3t1_5, /g3t1_4, /g3t1_3, /g3t1_2, /g3t1_1
	# 	Given the /injector node is online
	# 	When I check if topics /uncertainty_/g3t1_1,/uncertainty_/g3t1_2,/uncertainty_/g3t1_3,/uncertainty_/g3t1_4,/uncertainty_/g3t1_5,/uncertainty_/g3t1_6,/log_uncertainty are inbound from /injector
	# 	Then /injector node is connected appropriately

	@topology @contract
	Scenario Outline: The uncertainty injector is wired to each body sensor
		Given the uncertainty injector is running
		Then the uncertainty injector should publish "uncertainty injection" to <sensor>
		
		Examples:
			| sensor          |
			| the oximeter    |
			| the ECG sensor  |
			| the thermometer |
			| the SBP sensor  |
			| the DBP sensor  |
			| the glucometer  |
	
	
	@topology @contract
	Scenario: The uncertainty injector is wired to the system log
		Given the uncertainty injector is running
		Then the uncertainty injector should publish "uncertainty log" to the system log

