Feature: Managing system adapts sensor sampling rate in response to reliability changes

	Scenario: Check if /enactor communicates with /reli_engine and /logger
		Given the /enactor node is online
		When I check if topics /strategy are inbound and /exception are outbound to /reli_engine
		And I check if topics /event are inbound and /log_adapt are outbound to /logger
		Then /enactor node is connected appropriately

	Scenario: Check if /logger communicates with /collector, /param_adapter, /enactor, /data_access, /injector
		Given the /logger node is online
		When I check if topics /log_uncertainty are inbound from /injector
		And I check if topics /log_adapt are inbound and /event are outbound to /enactor
		And I check if topics /log_event,/log_status,/log_energy_status are inbound from /collector
		And I check if topics /reconfigure are outbound to /param_adapter
		And I check if topics /persist are outbound to /data_access
		Then /logger node is connected appropriately

# Novos cenarios
  Scenario: Sampling rate increases when sensor reliability falls below the threshold (G4/G5)
    Given the managing system is monitoring the reliability of sensor /g3t1_1
    When sensor /g3t1_1 repeatedly reports a 'fail' status
    Then an adaptation command increasing the sampling rate of sensor /g3t1_1 should be issued

  Scenario: Sampling rate decreases after sensor reliability recovers (G4/G5)
    Given sensor /g3t1_1 is operating at an elevated sampling rate after a prior adaptation
    When the sensor reliability rises above the configured threshold
    Then an adaptation command reducing the sampling rate of sensor /g3t1_1 should be issued

  Scenario: A failed adaptation attempt is recorded in the system log (G4/G5)
    Given an adaptation command has been issued for sensor /g3t1_1
    When the adaptation cannot be delivered to the sensor
    Then a failure record for sensor /g3t1_1 should be available in the system log within 2 seconds

  Scenario: Managing system responds to reliability degradation within acceptable time (G4/G5)
    Given sensor /g3t1_1 is operating normally with stable reliability
    When sensor /g3t1_1 repeatedly reports a 'fail' status
    Then an adaptation command for sensor /g3t1_1 should be issued within 10 seconds

  @xfail
  Scenario: No adaptation is triggered when reliability is within the acceptable range (G4/G5)
    Given the /reli_engine node is computing reliability within the acceptable range
    And the /enactor node is active
    When the managing system evaluates the current reliability state
    Then the /reli_engine should not publish a new strategy to /strategy
    And the /enactor should not issue any adaptation command to log_adapt