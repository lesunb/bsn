# Propriedades e resultados: src/tg/apendices/apendice_b_propriedades_bdd.md
Feature: Ensure knowledge repository components are communicating correctly
	
	@topology @contract
	# Rastreabilidade BDD12: BSN-C06. Contrato estrutural complementar, relacionado à infraestrutura de P8.
	Scenario: The knowledge repository is wired to the system log and to the central hub
		Given the knowledge repository is running
		Then the knowledge repository should subscribe to "persistence" published by the system log
		And the knowledge repository should subscribe to "monitoring data" published by the central hub
