import ros_pytest
from pytest_bdd import scenarios, given, when, then, parsers
from test_sensor import SharedSensorTests
import rospy
from interface_map import SYSTEM_MAP
from conftest import check_topic_inbound_from_node, _node_topic_info
from asserts import is_node_receiving_multiple_topics, assert_node_is_online, is_node_publishing_to_topics
import pytest

scenarios("./features/target_system.feature")

topics = ['/oximeter_data', '/ecg_data', '/thermometer_data','/abps_data', '/abpd_data', '/glucosemeter_data']
sensors = ['/g3t1_1', '/g3t1_2', '/g3t1_3', '/g3t1_4', '/g3t1_5', '/g3t1_6']


@then('<sensor> should publish "vital sign data" to the central hub')
def sensor_publishes_vital_sign_data_to_central_hub(sensor):
    node_name = SYSTEM_MAP[sensor]
    sensor_topic = _node_topic_info(sensor)['topic']
    SharedSensorTests.assert_sensors_are_publishing_data(node_name, [sensor_topic])
    SharedSensorTests.assert_topic_has_data(sensor_topic)

    central_hub = SYSTEM_MAP['the central hub']
    is_receiving, missing_topics = is_node_receiving_multiple_topics(central_hub, [sensor_topic])
    assert is_receiving, "{} is missing data from these topics: {}".format(central_hub, missing_topics)

COLLECTOR_INPUT_TOPICS = ['/collect_event', '/collect_status', '/collect_energy_status']

@then(parsers.parse('<sensor> should publish "sensor log" to {target}'))
def sensor_publishes_log_to_log_collector(sensor, target):
    log_collector = SYSTEM_MAP[target]
    is_receiving, missing_topics = is_node_receiving_multiple_topics(log_collector, COLLECTOR_INPUT_TOPICS)
    assert is_receiving, "{} is missing data from these topics: {}".format(log_collector, missing_topics)


@then('the parameter adapter should publish "reconfiguration command" to <target>')
def parameter_adapter_publishes_reconfiguration_command(context, target):
    topic_name = SYSTEM_MAP['reconfiguration command'] + SYSTEM_MAP[target]
    check_topic_inbound_from_node(context, topic_name, SYSTEM_MAP['the parameter adapter'])

patient_response = {
    'oxigenation': None,
    'heart_rate': None,
    'abps': None,
    'abpd': None,
    'glucose': None,
}

vital_sign_service_key = {
    'blood oxygenation': 'oxigenation',
    'heart rate': 'heart_rate',
    'systolic blood pressure': 'abps',
    'diastolic blood pressure': 'abpd',
    'blood glucose': 'glucose',
}

@given('the patient simulator is generating vital signs for the monitored patient')
def patient_simulator_is_generating_vital_signs():
    assert_node_is_online(SYSTEM_MAP['the patient simulator'])

from services.srv import PatientData

def call_get_patient_data_service(sensor_type):
    rospy.wait_for_service('/getPatientData')
    try:
        get_patient_data = rospy.ServiceProxy('/getPatientData', PatientData)
        response = get_patient_data(sensor_type)
        patient_response[sensor_type] = response.data
        assert response.data != '', "No data received from /getPatientData service"
    except rospy.ServiceException as e:
        pytest.fail("Service call to /getPatientData failed: %s" % str(e))

@when('the current value of <vital sign> is requested')
def request_current_vital_sign_value(request):
    vital_sign = request.getfixturevalue('vital sign')
    call_get_patient_data_service(vital_sign_service_key[vital_sign])

@then('a value within the valid range of <vital sign> should be returned')
def vital_sign_value_within_valid_range(request):
    vital_sign = request.getfixturevalue('vital sign')
    sensor_type = vital_sign_service_key[vital_sign]
    assert patient_response[sensor_type] is not None, "/getPatientData service returned null response for {}".format(sensor_type)
