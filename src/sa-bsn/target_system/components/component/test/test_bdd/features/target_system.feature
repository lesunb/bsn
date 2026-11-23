# Propriedades e resultados: src/tg/apendices/apendice_b_propriedades_bdd.md
Feature: Ensure that central hub receives data from body sensors and publishes to data access node

	@topology
	# Rastreabilidade BDD22: BSN-C13. Contrato de comunicação complementar, relacionado a P7/P9.
	Scenario Outline: Each body sensor sends its readings to the central hub
		Given <sensor> is running
		Then <sensor> should publish "vital sign data" to the central hub
		
		Examples:
			| sensor          |
			| the oximeter    |
			| the ECG sensor  |
			| the thermometer |
			| the SBP sensor  |
			| the DBP sensor  |
			| the glucometer  |

	@topology
	# Rastreabilidade BDD23: BSN-C14. Contrato estrutural complementar de reconfiguração.
	Scenario Outline: The parameter adapter forwards reconfiguration commands to each target
		Given the parameter adapter is running
		Then the parameter adapter should publish "reconfiguration command" to <target>
		
		Examples:
			| target          |
			| the oximeter    |
			| the ECG sensor  |
			| the thermometer |
			| the SBP sensor  |
			| the DBP sensor  |
			| the glucometer  |
			| the central hub |

	@behavior @patient-simulator
	# Rastreabilidade BDD24: BSN-C15. Contrato complementar do simulador de paciente.
	Scenario Outline: The patient simulator returns a current value for each monitored vital sign
		Given the patient simulator is generating vital signs for the monitored patient
		When the current value of <vital sign> is requested
		Then a value within the valid range of <vital sign> should be returned
		
		Examples:
			| vital sign               |
			| blood oxygenation        |
			| heart rate               |
			| systolic blood pressure  |
			| diastolic blood pressure |
			| blood glucose            |

