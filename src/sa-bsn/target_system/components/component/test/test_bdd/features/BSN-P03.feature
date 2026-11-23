# Propriedades e resultados: src/tg/apendices/apendice_b_propriedades_bdd.md
# Feature: BSN-P03: Whenever the patients' health status is on high risk and an emergency has been detected it implies that is less or equal 250 (ms)

# 	Scenario: Successful Sensor Execution
# 		Given that nodes thermometer and central hub are online
# 		When I listen to thermometer
# 		And thermometer sends data with high risk
# 		Then Central hub will detect an emergency in less than 250 ms

# 	Scenario: Overloaded sensor data
# 		Given that nodes thermometer and central hub are online
# 		When I listen to thermometer
# 		And thermometer sends low-risk data with high frequency
# 		But thermometer sends data with high risk
# 		Then Central Hub will experience delayed emergency detection

Feature: Emergency detection (BSN-P03) A high-risk vital sign reading is escalated to an emergency within 250 ms.
	
	@timing @bsn-p03
	# Rastreabilidade BDD01: BSN-P03. Retomada de P3, com fronteira de observação adaptada.
	Scenario: An emergency is reported within 250 ms of a high-risk reading (BSN-P03)
		Given the patient is being monitored by the thermometer
		When the thermometer reports a vital sign reading in the high-risk range
		Then the central hub should report an emergency within 250 ms of that reading

	@timing @sad-path @bsn-p03
	# Rastreabilidade BDD02: BSN-P03. Variante local sob carga de P3.
	Scenario: An emergency is reported within 250 ms even while the sensor is under sustained load (BSN-P03)
		Given the thermometer is reporting low-risk readings at its maximum sampling rate
		When the thermometer reports a vital sign reading in the high-risk range
		Then the central hub should report an emergency within 250 ms of that reading
