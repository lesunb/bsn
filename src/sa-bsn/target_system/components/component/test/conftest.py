from pytest_bdd import given, parsers, when, then
import rospy
import rosnode
import pytest
from asserts import is_node_receiving_multiple_topics, assert_node_is_online, is_node_publishing_to_topics
from parsers import capture_topic_data, process_real_time_topics

FULL_SYSTEM = ['/collector', '/param_adapter',
               '/g3t1_1', '/g3t1_2', '/g3t1_3', 
               '/g3t1_4', '/g3t1_5', '/g3t1_6', 
               '/g4t1']

@pytest.fixture(scope='module')
def context():
    """
    Fixture to hold context data for BDD tests.
    """
    return {}

# Shared step definitions

@given("the ROS environment is on")
def ros_environment_is_on():
    rospy.sleep(1)  # Give ROS some time to initialize
    nodes = rosnode.get_node_names()

    assert len(nodes) > 0, "ROS environment is not running or no nodes are active."

@given(parsers.parse("the {node_name} node is online"))
def node_is_online(context, node_name):
    context['is_node_online'] = True
    assert_node_is_online(node_name)

@when(parsers.parse("I check if topics {topic} are outbound to {node}"))
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

@when(parsers.parse("I check if topics {topic} are inbound from {node}"))
def check_topic_inbound_from_node(context, topic, node):
    if ',' in topic:
        topic_list = topic.split(',')
    else:
        topic_list = [topic]
    is_receiving, missing_topics = is_node_publishing_to_topics(node, topic_list)
    context['is_node_online'] = missing_topics == []
    assert is_receiving, "{} is missing data from these topics: {}".format(node, missing_topics)

@when(parsers.parse("I check if topics {topic} are inbound and {topic_outbound} are outbound to {node}"))
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

@then(parsers.parse("{node_name} node is connected appropriately"))
def node_connected_appropriately(context, node_name):
    assert context['is_node_online'], "/{} node is not connected appropriately".format(node_name)

@when('I listen to thermometer')
def listen_to_thermometer(context):
    # Aguarda thread de erro terminar se existir
    print('Listening to thermometer...')
    if 'error_publisher_thread' in context:
        print('error?')
        context['error_publisher_thread'].join(timeout=3.0)
    
    context['sensor_data'] = {}
    context['found_high_risk'] = []
    context['target_system_data'] = {}
    context['non_sensor'] = {}
    topics = [
        '/thermometer_data',
        '/collect_energy_status',
        '/persist',
        '/log_energy_status',
        '/TargetSystemData'
    ]
    print('Topics to listen: {}'.format(topics))

    process_real_time_topics(context, capture_topic_data, topics)
    print('finished listening to thermometer.')
