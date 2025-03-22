SENSOR_NODE = {  
    'oximeter': '/g3t1_1',
    'ecg': '/g3t1_2',
    'thermometer': '/g3t1_3',
    'abps': '/g3t1_4',
    'abpd': '/g3t1_5',
    'glucosemeter': '/g3t1_6'
    }
FULL_SYSTEM = ['/collector', '/param_adapter',
               '/g3t1_1', '/g3t1_2', '/g3t1_3', 
               '/g3t1_4', '/g3t1_5', '/g3t1_6', 
               '/g4t1']
REDUCED_SYSTEM = ['/collector', '/param_adapter','/g3t1_3', '/g4t1', '/patient_data_service']

PERSISTENCE_NODES = [
    "/g4t1",
    "/collector",
    "/param_adapter",
    "/g3t1_3",
    "/data_access",
    "/logger"
]
PERSISTANCE_TOPICS = [
        '/thermometer_data',
        '/collect_energy_status',
        '/persist',
        '/log_energy_status',
        '/TargetSystemData'
    ]
NON_SENSOR_TOPICS = [
        '/collect_energy_status',
        '/persist',
        '/log_energy_status',
        '/TargetSystemData'
]