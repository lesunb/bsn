from behave import given, when, then
import subprocess
from utils.parsers import process_real_time_topics, capture_topic_data, format_debug_data, parse_topic_data
from utils.constants import PERSISTENCE_NODES, PERSISTANCE_TOPICS
from utils.asserts import kill_node

REDUCED_SYSTEM_NODES = [
    "thermometer",
    "central_hub"
]

def node_is_active(node_name):
    """Check if a ROS node is active."""
    result = subprocess.run(['rosnode', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    node_list = result.stdout.decode('utf-8').splitlines()
    return node_name in node_list

def check_nodes_online(node_list):
    """Check if all required nodes are online."""
    for node in node_list:
        assert node_is_active(node), f"Node {node} is not online"

@given('that persistence system is online')
def step_given_reduced_system_nodes_online(context):
    check_nodes_online(PERSISTENCE_NODES)

@given('nodes are online')
def step_given_all_persistence_nodes_online(context):
    check_nodes_online(PERSISTENCE_NODES)

@when('I listen to thermometer data')
def step_when_i_listen_to_thermometer(context):
    context.sensor_data = {}
    context.found_high_risk = []
    context.target_system_data = {}
    context.non_sensor = {}
    topics = [
        
        '/thermometer_data',
        '/collect_energy_status',
        '/persist',
        '/log_energy_status',
        '/TargetSystemData'
    ]

    process_real_time_topics(context, capture_topic_data, topics)
    #print(f'non sensor data: {format_debug_data(context.non_sensor)}')
    print(context.non_sensor)
@when('I send data to collector')
def step_when_send_data_to_collector(context):
    """Simulate sending data to the collector."""
    assert '/g3t1_3' in context.non_sensor['/collect_energy_status']['source'], f'No data detected in /collect_energy_status.'

@when('collector receives collect_? topic')
def step_when_collector_receives_collect_topic(context):
    """Simulate collector receiving the collect topic."""
    assert context.data_sent_to_collector, "Collector has not received any data."

@then('the data will be in persist topic')
def step_then_data_persisted(context):
    """Simulate data persistence."""
    assert 'Status' in context.non_sensor['/persist']['type'], f"Data was not sent to collector, so it cannot be persisted."
    print(context.non_sensor['/persist']['type'])


@when('a database error prevents persistence')
def step_when_database_error_occurs(context):
    """Simulate a database error preventing persistence."""
    kill_node('/logger')

@then('the system must log a persistence failure')
def step_then_system_logs_failure(context):
    """Ensure the system logs a persistence failure."""
    energyStatus = parse_topic_data('/log_energy_status')
    print(f'energyStatus: {energyStatus}')
    assert all(val == '' for val in energyStatus['target'])
    persist_topic = parse_topic_data('/persist')
    print(f'persist topic: {persist_topic}')
    assert persist_topic is None

