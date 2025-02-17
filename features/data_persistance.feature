Feature: Data Persistence (BSN-P08) - Whether the sensor node has collected some data, eventually the bodyhub will persist it.

	Scenario: Data Persisted Successfully (Happy Path)
		# Given that nodes thermometer and central hub are online
		# When I listen to thermometer data
		# And I send data to collector
		# Then the data will be in persist topic
		Given nodes are online:
			| Nodes         |
			| g4t1      	|
			| collector     |
			| param adapter |
			| g3t1_3     	|
			| data access   |
			| Logger     	|
		When collector receives collect_? topic
		Then the data will be received in logger
		And the data will be in persist topic

	Scenario: Data Not Persisted (Sad Path)
		# Given that nodes thermometer and central hub are online
		# When I listen to thermometer data
		# And I send data to collector
		# But a database error prevents persistence
		# Then the system must log a persistence failure
		Given nodes are online:
			| Nodes         |
			| g4t1      	|
			| collector     |
			| param adapter |
			| g3t1_3     	|
			| data access   |
			| Logger     	|
		And the sensor node has collected data
		When collector receives collect_? topic
		And a database error prevents persistence
		Then the data will not be persisted
		And the system must log a persistence failure
		And the system may attempt a retry