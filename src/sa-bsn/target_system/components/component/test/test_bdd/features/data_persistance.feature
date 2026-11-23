# Propriedades e resultados: src/tg/apendices/apendice_b_propriedades_bdd.md
Feature: Data Persistence (BSN-P08) - Whether the sensor node has collected some data, eventually the bodyhub will persist it.

	@behavior @bsn-p08 @persistence
	# Rastreabilidade BDD06: BSN-P08. Retomada de P8; enunciado atual exige recuperação do valor.
	Scenario: A vital sign reading collected by a sensor is persisted in the knowledge repository (BSN-P08)
		Given the patient is being monitored by the thermometer
		When the thermometer reports a new vital sign reading
		Then that reading should be retrievable from the knowledge repository with the value reported

	@behavior @sad-path @bsn-p08 @persistence @gap
	# xfail (ver PERSISTENCE_FAILURE_GAP_REASON): o DataAccess.cpp nunca teve branch de falha de armazenamento, entao nao ha
	# caminho "errado" a corrigir. O antigo `'fail' in content` passava por ruido do /g4t1 e porque o kill do /logger nunca
	# funciona.
	# Rastreabilidade BDD07: BSN-C03. Complementar de falha de armazenamento, relacionada a P8.
	Scenario: A persistence failure is recorded when the knowledge repository cannot store a reading (BSN-P08)
		Given the knowledge repository is experiencing storage failures
		When the thermometer reports a new vital sign reading
		Then a persistence failure record identifying that reading should be available in the system log
