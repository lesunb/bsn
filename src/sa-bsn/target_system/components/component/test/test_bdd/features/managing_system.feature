Feature: Managing system adapts sensor sampling rate in response to reliability changes

  @topology
  Scenario: The adaptation enactor exchanges adaptation strategies with the reliability engine
    Given the adaptation enactor is running
    Then the adaptation enactor should subscribe to "adaptation strategy" published by the reliability engine
    And the adaptation enactor should publish "adaptation exception" to the reliability engine
  
  
  @topology
  Scenario: The adaptation enactor exchanges adaptation records with the system log
    Given the adaptation enactor is running
    Then the adaptation enactor should subscribe to "log event" published by the system log
    And the adaptation enactor should publish "adaptation log" to the system log

  @topology
  Scenario Outline: The system log receives each topic collected by the log collector
    Given the system log is running
    Then the system log should subscribe to <topic> published by the log collector

    Examples:
      | topic                |
      | sensor event         |
      | sensor status        |
      | sensor energy status |
  
  @topology
  Scenario: The system log sends reconfiguration requests to the parameter adapter
    Given the system log is running
    Then the system log should publish "reconfiguration request" to the parameter adapter

  @behavior @g4-g5
  Scenario: Sampling rate increases when sensor reliability falls below the threshold (G4/G5)
    Given the managing system is monitoring the reliability of the oximeter
    When the oximeter repeatedly reports a 'fail' status
    Then an adaptation command increasing the sampling rate of the oximeter should be issued

  @behavior @g4-g5
  Scenario: Sampling rate decreases after sensor reliability recovers (G4/G5)
    Given the oximeter is operating at an elevated sampling rate
    When the reliability of the oximeter rises above the threshold
    Then an adaptation command reducing the sampling rate of the oximeter should be issued

  @timing @g4-g5
  Scenario: An adaptation command is issued within 10 seconds after reliability degradation (G4/G5)
    Given the oximeter is operating normally with stable reliability
    When the oximeter repeatedly reports a 'fail' status
    Then an adaptation command for the oximeter should be issued within 10 seconds

  @xfail @behavior @g4-g5
  # Razão técnica: o controlador SA-BSN é um otimizador contínuo (kp=150, limites 0.1-40 Hz, margem 0.02); com r_curr = 1.0
  # emite comandos de redução em vez de ficar em silêncio. Mantido deliberadamente: se passar em ROS 2, o comportamento
  # do controlador mudou e isso precisa aparecer no relatório de migração.
  Scenario: No adaptation is triggered while sensor reliability stays above the threshold (G4/G5)
    Given the managing system is monitoring the reliability of the oximeter
    When the reliability of the oximeter stays above the threshold
    Then no adaptation command for the oximeter should be issued

  @behavior @logging @g4-g5
  Scenario: A failed adaptation attempt is recorded in the system log (G4/G5)
    Given the oximeter cannot receive adaptation commands
    When an adaptation command is issued for the oximeter
    Then the adaptation command should be recorded in the system log even though the oximeter cannot receive it
