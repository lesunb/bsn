Feature: Ensure knowledge repository components are communicating correctly

	Scenario: Check if /data_access communicates with /g4t1, /logger
		Given the /data_access node is online
		When I check if topics /persist are inbound from /logger
		And I check if topics /TargetSystemData are inbound from /g4t1
		Then /data_access node is connected appropriately