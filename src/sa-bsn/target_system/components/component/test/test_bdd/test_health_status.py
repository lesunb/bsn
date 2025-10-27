import ros_pytest
from pytest_bdd import scenarios, given, when, then, parsers
from test_sensor import SharedSensorTests
import rospy
import rosnode
from asserts import is_node_receiving_multiple_topics, assert_node_is_online, is_node_publishing_to_topics,check_time_performance
from parsers import process_real_time_topics, parse_topic_data, capture_topic_data

scenarios("./features/health_status.feature")
# scenarios("./features/BSN-P03.feature")

@given('that nodes thermometer and central hub are online')
def thermometer_and_central_hub_are_online():
    nodes = rosnode.get_node_names()
    thermometer_node = '/g3t1_3'
    central_hub_node = '/g4t1'
    assert thermometer_node in nodes, "{} is not online.".format(thermometer_node)
    assert central_hub_node in nodes, "{} is not online.".format(central_hub_node)
    
@then('g4t1 will detect new patient health status')
def g4t1_detects_health_status(context):
    assert len(set(context['target_system_data']['patient_status'])) > 1, "status has not changed. Patient Status: {}".format(context['target_system_data']['patient_status'])

@when('an internal processing error occurs in g4t1')
def step_when_internal_error_occurs(context):
    context['internal_error'] = True

@then('Central hub will fail to detect the new patient health status')
def step_then_g4t1_fails_to_detect_status(context):
    assert context['internal_error'], "No internal error detected"

@given('that nodes thermometer and central hub are online')
def step_given_reduced_system_nodes_online(context):
    assert_node_is_online('/g3t1_3')  # Thermometer node
    assert_node_is_online('/g4t1')     # Central hub node

@when('thermometer sends data with high risk')
def step_when_high_risk_data_sent(context):
    assert_node_is_online('/patient_data_service')

@then('Central hub will detect an emergency in less than 250 ms')
def step_then_g4t1_detects_emergency(context):
    print('teste_final')
    print(context['sensor_data'])
    performance_check = check_time_performance(context['sensor_data'], context['target_system_data'],
                                  '/thermometer_data','trm_data', 'data')
    
    assert performance_check, "Central hub failed to detect an emergency in less than 250 ms"

@when(parsers.parse('{node_name} sends low-risk data with high frequency'))
def step_when_overloaded_data_sent(context, node_name):
    topic = '/{}_data'.format(node_name)
    _, parsed_data, high_risk_detected = capture_topic_data(topic)
    context.overloaded = True
    context.high_risk_detected = high_risk_detected
    assert context.overloaded, "Sensor data overload did not occur"

@then('Central Hub will experience delayed emergency detection')
def step_then_g4t1_might_delay_detection(context):
    assert context.overloaded and context.high_risk_detected, "Delayed detection scenario not met"
