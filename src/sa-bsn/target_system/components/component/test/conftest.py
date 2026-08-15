from pytest_bdd import given, parsers, when, then
import rospy
import rosnode
import pytest
from asserts import is_node_receiving_multiple_topics, assert_node_is_online, is_node_publishing_to_topics, node_is_active
from parsers import capture_topic_data, process_real_time_topics
from interface_map import SYSTEM_MAP

FULL_SYSTEM = ['/collector', '/param_adapter',
               '/g3t1_1', '/g3t1_2', '/g3t1_3', 
               '/g3t1_4', '/g3t1_5', '/g3t1_6', 
               '/g4t1']
SENSORS = ['/g3t1_1', '/g3t1_2', '/g3t1_3', 
               '/g3t1_4', '/g3t1_5', '/g3t1_6']

@pytest.fixture(scope='module')
def context():
    """
    Fixture to hold context data for BDD tests.
    """
    return {}

# Shared step definitions

@given("the ROS environment is on") # remover
def ros_environment_is_on():
    rospy.sleep(1)  # Give ROS some time to initialize
    nodes = rosnode.get_node_names()

    assert len(nodes) > 0, "ROS environment is not running or no nodes are active."

@given(parsers.parse("{node_name} is running"))
@given(parsers.parse("the {node_name} node is online")) # remover
def node_is_online(context, node_name):
    assert_node_is_online(SYSTEM_MAP[node_name])
    context['is_node_online'] = True

@when(parsers.parse("I check if topics {topic} are outbound to {node}")) # remover
def check_topic_outbound_to_node(context, topic, node):
    if ',' in topic:
        topic_list = topic.split(',')
    else:
        topic_list = [topic]
    is_receiving, missing_topics = is_node_receiving_multiple_topics(node, topic_list)
    context['is_node_online'] = missing_topics == []
    print('is_receiving: {}, for topic {} and node {}'.format(is_receiving, topic, node))
    print('missing_topics: {}'.format(missing_topics))
    assert is_receiving, "{} is missing data from these topics: {}".format(node, missing_topics)

@when(parsers.parse("I check if topics {topic} are inbound from {node}")) # remover
def check_topic_inbound_from_node(context, topic, node):
    if ',' in topic:
        topic_list = topic.split(',')
    else:
        topic_list = [topic]
    is_receiving, missing_topics = is_node_publishing_to_topics(node, topic_list)
    context['is_node_online'] = missing_topics == []
    assert is_receiving, "{} is missing data from these topics: {}".format(node, missing_topics)

@when(parsers.parse("I check if topics {topic} are inbound and {topic_outbound} are outbound to {node}")) # remover
def check_topic_inbound_and_outbound(context, topic, topic_outbound, node):
    rospy.sleep(3)  # Small delay to ensure topics are being published/subscribed
    print('check')
    if ',' in topic:
        topic_list = topic.split(',')
    else:
        topic_list = [topic]
    is_receiving, missing_topics = is_node_publishing_to_topics(node, topic_list)

    if ',' in topic_outbound:
        topic_outbound_list = topic_outbound.split(',')
    else:
        topic_outbound_list = [topic_outbound]
    is_publishing, missing_outbound_topics = is_node_receiving_multiple_topics(node, topic_outbound_list)

    context['is_node_online'] = missing_topics == [] and missing_outbound_topics == []
    assert is_receiving, "{} is missing data from these topics: {}".format(node, missing_topics)
    assert is_publishing, "{} is missing data from these topics: {}".format(node, missing_topics)

@then(parsers.parse("{node_name} node is connected appropriately")) # remover
def node_connected_appropriately(context, node_name):
    assert context['is_node_online'], "/{} node is not connected appropriately".format(node_name)


# refactored

SENSOR_TOPIC_INFO = {
    'g3t1_1': {'topic': '/oximeter_data',    'data_key': 'oxi_data',  'risk_key': 'oxi_risk'},
    'g3t1_2': {'topic': '/ecg_data',          'data_key': 'ecg_data', 'risk_key': 'ecg_risk'},
    'g3t1_3': {'topic': '/thermometer_data',  'data_key': 'trm_data', 'risk_key': 'trm_risk'},
    'g3t1_4': {'topic': '/abps_data',         'data_key': 'abps_data', 'risk_key': 'abps_risk'},
    'g3t1_5': {'topic': '/abpd_data',         'data_key': 'abpd_data', 'risk_key': 'abpd_risk'},
    'g3t1_6': {'topic': '/glucosemeter_data', 'data_key': 'glc_data', 'risk_key': 'glc_risk'},
}

@given(parsers.parse('the patient is being monitored by {sensor}'))
@given('the patient is being monitored by <sensor>')
def step_given_patient_monitored_by_sensor(context, sensor):
    node_is_active([SYSTEM_MAP[sensor], SYSTEM_MAP['the central hub']])

def _sensor_topic_info(sensor):
    """Resolve a Gherkin sensor label (e.g. 'the oximeter') to its topic info via SYSTEM_MAP."""
    node_name = SYSTEM_MAP[sensor].lstrip('/')
    return SENSOR_TOPIC_INFO[node_name]

def _send_data_to_collector(context):
    """Simulate sending data to the collector."""
    assert context['sensor'] in context['non_sensor']['/collect_energy_status']['source'], 'No data detected in /collect_energy_status.'

@when('I listen to thermometer') # remover
@when('<sensor> reports a new vital sign reading')
@when(parsers.parse('{sensor} reports a new vital sign reading'))
def step_when_sensor_reports_new_reading(context, sensor):
    context['sensor'] = SYSTEM_MAP[sensor]
    context['sensor_data'] = {}
    context['found_high_risk'] = []
    context['target_system_data'] = {}
    context['non_sensor'] = {}

    topic = _sensor_topic_info(sensor)['topic']
    process_real_time_topics(context, capture_topic_data, [
        topic,         
        '/collect_energy_status',
        '/persist',
        '/log_energy_status',
        '/TargetSystemData'
    ])
    print('context: {}'.format(context))

    _send_data_to_collector(context)
    if context.get('simulate_persistence_failure'):
        _database_error_occurs(context)

def _database_error_occurs(context):
    """Simulate a database error preventing persistence."""
    rosnode.kill_nodes('/logger')
    rospy.sleep(2)

@then(parsers.parse('{node} should publish "{topic}" to {node_target}'))
def then_publish_to_node(context, node, topic, node_target):
    check_topic_inbound_from_node(context, SYSTEM_MAP[topic], SYSTEM_MAP[node])

@then(parsers.parse('{node} should subscribe to <topic> published by {node_origin}'))
@then(parsers.parse('{node} should subscribe to "{topic}" published by {node_origin}'))
def then_subscribe_to_topic(context, node, topic, node_origin):
    check_topic_outbound_to_node(context, SYSTEM_MAP[topic], SYSTEM_MAP[node])

@then(parsers.parse('{node} should subscribe to "{inbound_topic}" and publish "{outbound_topic}" to {node_target}'))
def then_subscribe_and_publish_to_reliability_engine(context, node, inbound_topic, outbound_topic):
    check_topic_inbound_and_outbound(context, SYSTEM_MAP[inbound_topic], SYSTEM_MAP[outbound_topic], SYSTEM_MAP[node])