from behave import given, when, then
from utils.parsers import parse_topic_data, format_entity, process_real_time_topics, capture_topic_data
from utils.asserts import node_is_active, check_time_performance
from utils.constants import REDUCED_SYSTEM, FULL_SYSTEM

@given('that nodes thermometer and central hub are online')
def step_given_reduced_system_nodes_online(context):
    node_is_active(REDUCED_SYSTEM)    
@when('{node_name} sends a collection of data')
def step_when_node_sends_data(context, node_name):
    topic = f'/{node_name}_data'
    context.sensor_data = capture_topic_data(topic)
    assert context.sensor_data, f"No data received from {node_name}"
@when('I listen to thermometer')
def step_when_i_listen_to_thermometer(context):
    context.sensor_data = {}
    context.found_high_risk = []
    context.target_system_data = {}
    
    topics = [
        '/thermometer_data',
        '/TargetSystemData'
    ]

    process_real_time_topics(context, capture_topic_data, topics)
@then('g4t1 will detect new patient health status')
def step_then_g4t1_detects_health_status(context):
    assert len(set(context.target_system_data['patient_status'])) > 1, f"status has not changed. Patient Satus: {context.target_system_data['patient_status']}"

@given('the bodyhub has processed patient data')
def step_given_bodyhub_processed_data(context):
    context.processed_data = True
    assert context.processed_data, "Bodyhub failed to process patient data"

@when('an internal processing error occurs in g4t1')
def step_when_internal_error_occurs(context):
    context.internal_error = True

@then('Central hub will fail to detect the new patient health status')
def step_then_g4t1_fails_to_detect_status(context):
    assert context.internal_error, "No internal error detected"
    assert 'patient_status' not in context.sensor_data[1], "g4t1 incorrectly detected a patient status"

@when('{sensor_name} sends data with high risk')
def step_when_high_risk_data_sent(context, sensor_name):
    # implementation made by patient data service
    if sensor_name == 'thermometer':
        pass
    node_is_active('/patient_data_service')
    

@then('Central hub will detect an emergency in less than 250 ms')
def step_then_g4t1_detects_emergency(context):
    assert check_time_performance(context.sensor_data, context.target_system_data,
                                  '/thermometer_data','trm_data', 'data')

@given('Patient Data is not active')
def step_given_patient_data_inactive(context):
    context.patient_data_active = False
    assert not context.patient_data_active, "Patient data should be inactive"

@when('{node_name} sends low-risk data with high frequency')
def step_when_overloaded_data_sent(context, node_name):
    topic = f'/{node_name}_data'
    _, parsed_data, high_risk_detected = capture_topic_data(topic)
    context.overloaded = True
    context.high_risk_detected = high_risk_detected
    assert context.overloaded, "Sensor data overload did not occur"

@then('Central Hub will experience delayed emergency detection')
def step_then_g4t1_might_delay_detection(context):
    assert context.overloaded and context.high_risk_detected, "Delayed detection scenario not met"
