import ros_pytest
from pytest_bdd import scenarios, given, when, then, parsers
from test_sensor import SharedSensorTests
import rospy
import rosnode
from asserts import is_node_receiving_multiple_topics, node_is_active, is_node_publishing_to_topics,check_time_performance
from parsers import process_real_time_topics, parse_topic_data, capture_topic_data

scenarios("./features/data_persistance.feature")

PERSISTENCE_NODES = [
    "/g4t1",
    "/collector",
    "/param_adapter",
    "/g3t1_3",
    "/data_access",
    "/logger"
]

@given('that persistence system is online')
def node_is_online():
    node_is_active(PERSISTENCE_NODES)

@when('I send data to collector')
def step_when_send_data_to_collector(context):
    """Simulate sending data to the collector."""
    assert '/g3t1_3' in context['non_sensor']['/collect_energy_status']['source'], 'No data detected in /collect_energy_status.'

@then('the data will be in persist topic')
def step_then_data_persisted(context):
    """Simulate data persistence."""
    assert 'Status' in context['non_sensor']['/persist']['type'], 'Data was not sent to collector, so it cannot be persisted.'

@when('a database error prevents persistence')
def step_when_database_error_occurs(context):
    """Simulate a database error preventing persistence."""
    rosnode.kill_nodes('/logger')
    rospy.sleep(2)  

@then('the system must log a persistence failure')
def step_then_system_logs_failure(context):
    """Ensure the system logs a persistence failure."""
    energyStatus = parse_topic_data('/log_energy_status')
    assert all(val == '' for val in energyStatus['target'])
    persist_topic = parse_topic_data('/persist')
    assert 'fail' in persist_topic['content']
