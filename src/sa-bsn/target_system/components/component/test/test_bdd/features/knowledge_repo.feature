Feature: Ensure knowledge repository components are communicating correctly
	
	@topology @contract
	Scenario: The knowledge repository is wired to the system log and to the central hub
		Given the knowledge repository is running
		Then the knowledge repository should subscribe to "persistence" published by the system log
		And the knowledge repository should subscribe to "monitoring data" published by the central hub
