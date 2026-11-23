SYSTEM_MAP = {
    'the central hub': '/g4t1',

	# system
	'the managing system': ['/reli_engine', '/enactor', '/logger', '/param_adapter'],
	'the reliability engine': '/reli_engine',
	'the adaptation enactor': '/enactor',
	'the system log': '/logger',
	'the parameter adapter': '/param_adapter',
	'the log collector': '/collector',
	'the uncertainty injector': '/injector',
	'monitoring data': '/TargetSystemData',

	'adaptation strategy': '/strategy',
	'adaptation exception': '/exception',

	'log event': '/event', 
	'adaptation log': '/log_adapt',
	'sensor event':'/log_event',
	'sensor status':'/log_status',
	'sensor energy status':'/log_energy_status',
	'reconfiguration request':'/reconfigure',
	'reconfiguration command':'/reconfigure_',

	# knowledge repository
	'the knowledge repository': '/data_access',

	# patient simulator
	'the patient simulator': '/patient',

	# sensores
	'the oximeter': '/g3t1_1',
	'the ECG sensor': '/g3t1_2',
	'the thermometer': '/g3t1_3',
	'the SBP sensor': '/g3t1_4',
	'the DBP sensor': '/g3t1_5',
	'the glucometer': '/g3t1_6',

	# topicos
	'uncertainty injection': '/uncertainty_',
	'uncertainty log': '/log_uncertainty',
	'persistence': '/persist',
}
