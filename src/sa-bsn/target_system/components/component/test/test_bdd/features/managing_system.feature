# Propriedades e resultados: src/tg/apendices/apendice_b_propriedades_bdd.md
Feature: Managing system adapts sensor sampling rate in response to reliability changes

  @topology
  # Rastreabilidade BDD13: BSN-C07. Contrato estrutural complementar.
  Scenario: The adaptation enactor exchanges adaptation strategies with the reliability engine
    Given the adaptation enactor is running
    Then the adaptation enactor should subscribe to "adaptation strategy" published by the reliability engine
    And the adaptation enactor should publish "adaptation exception" to the reliability engine
  
  
  @topology
  # Rastreabilidade BDD14: BSN-C07. Contrato estrutural complementar.
  Scenario: The adaptation enactor exchanges adaptation records with the system log
    Given the adaptation enactor is running
    Then the adaptation enactor should subscribe to "log event" published by the system log
    And the adaptation enactor should publish "adaptation log" to the system log

  @topology
  # Rastreabilidade BDD15: BSN-C07. Contrato estrutural complementar.
  Scenario Outline: The system log receives each topic collected by the log collector
    Given the system log is running
    Then the system log should subscribe to <topic> published by the log collector

    Examples:
      | topic                |
      | sensor event         |
      | sensor status        |
      | sensor energy status |
  
  @topology
  # Rastreabilidade BDD16: BSN-C07. Contrato estrutural complementar.
  Scenario: The system log sends reconfiguration requests to the parameter adapter
    Given the system log is running
    Then the system log should publish "reconfiguration request" to the parameter adapter

  @behavior @g4-g5
  # Rastreabilidade BDD17: BSN-C08. Critério local de adaptação por confiabilidade; G4/G5 local.
  Scenario: Sampling rate increases when sensor reliability falls below the threshold (G4/G5)
    Given the managing system is monitoring the reliability of the oximeter
    And the current publication rate of the oximeter is measured
    When the oximeter repeatedly reports a 'fail' status
    Then an adaptation command increasing the sampling rate of the oximeter should be issued
    And a record of an adaptation command increasing the sampling rate of the oximeter should reach the persistence channel
    And the observed publication rate of the oximeter should increase


  @behavior @g4-g5
  # Rastreabilidade BDD18: BSN-C09. Critério local de adaptação por confiabilidade; G4/G5 local.
  Scenario: Sampling rate decreases after sensor reliability recovers (G4/G5)
    Given the oximeter is operating at an elevated sampling rate
    When the reliability of the oximeter rises above the threshold
    Then an adaptation command reducing the sampling rate of the oximeter should be issued
    And the observed publication rate of the oximeter should decrease

  @timing @g4-g5
  # Rastreabilidade BDD19: BSN-C10. Critério temporal local; G4/G5 local.
  Scenario: An adaptation command is issued within 10 seconds after reliability degradation (G4/G5)
    Given the oximeter is operating normally with stable reliability
    When the oximeter repeatedly reports a 'fail' status
    Then an adaptation command for the oximeter should be issued within 10 seconds

  @xfail @behavior @g4-g5
  # Razão técnica: o controlador SA-BSN é um otimizador contínuo (kp=150, limites 0.1-40 Hz, margem 0.02); com r_curr = 1.0
  # emite comandos de redução em vez de ficar em silêncio. Mantido deliberadamente: se passar em ROS 2, o comportamento
  # do controlador mudou e isso precisa aparecer no relatório de migração.
  # Rastreabilidade BDD20: BSN-C11. Expectativa complementar não atendida; G4/G5 local.
  Scenario: No adaptation is triggered while sensor reliability stays above the threshold (G4/G5)
    Given the managing system is monitoring the reliability of the oximeter
    When the reliability of the oximeter stays above the threshold
    Then no adaptation command for the oximeter should be issued

  @behavior @logging @g4-g5
  # Rastreabilidade BDD21: BSN-C12. Critério complementar de registro; G4/G5 local.
  Scenario: A failed adaptation attempt is recorded in the system log (G4/G5)
    Given the oximeter cannot receive adaptation commands
    When an adaptation command is issued for the oximeter
    Then the adaptation command should be recorded in the system log even though the oximeter cannot receive it
