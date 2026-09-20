import ros_pytest
import pytest
from pytest_bdd import given, when, then, parsers, scenario
from test_sensor import SharedSensorTests
import rospy
import rosnode
from asserts import is_node_receiving_multiple_topics, node_is_active, is_node_publishing_to_topics,check_time_performance
from parsers import process_real_time_topics, parse_topic_data, capture_topic_data

FEATURE_FILE = "./features/data_persistance.feature"

PERSISTENCE_NODES = [
    "/g4t1",
    "/collector",
    "/param_adapter",
    "/g3t1_3",
    "/data_access",
    "/logger"
]

# Individual @scenario per test (not bulk scenarios()) so @pytest.mark.xfail can attach to a collected item;
# same style as bsn_ros2's test_data_persistance.py and test_injector.py.

@scenario(FEATURE_FILE, "A vital sign reading collected by a sensor is persisted in the knowledge repository (BSN-P08)")
def test_reading_persisted_in_knowledge_repository():
    pass


PERSISTENCE_FAILURE_GAP_REASON = (
    "gap, not a regression: DataAccess.cpp has no storage-failure branch (no 'PersistenceFailure' type). "
    "rosnode.kill_nodes('/logger') never kills the node mid-scenario, and the old 'fail' check passed only via "
    "/g4t1's unrelated 'fail' Status. See bsn_ros2's features/DATA_PERSISTANCE_GAPS.md"
)


@pytest.mark.xfail(reason=PERSISTENCE_FAILURE_GAP_REASON)
@scenario(FEATURE_FILE, "A persistence failure is recorded when the knowledge repository cannot store a reading (BSN-P08)")
def test_persistence_failure_recorded():
    pass


def node_is_online():
    node_is_active(PERSISTENCE_NODES)

def step_then_data_persisted(context):
    """Simulate data persistence."""
    assert 'Status' in context['non_sensor']['/persist']['type'], 'Data was not sent to collector, so it cannot be persisted.'


def step_then_system_logs_failure(context):
    """Ensure the system logs a persistence failure identifying the reading that failed (what the Gherkin asks for).
    Expected to fail today: nothing in this codebase publishes a 'PersistenceFailure' type."""
    persist_topic = parse_topic_data('/persist')
    failure_sources = {
        source for source, record_type in zip(persist_topic.get('source', ()), persist_topic.get('type', ()))
        if record_type == 'PersistenceFailure'
    }
    assert failure_sources, (
        "No PersistenceFailure record was logged while the knowledge "
        "repository was experiencing storage failures: {0}".format(persist_topic)
    )
    assert context['sensor'] in failure_sources, (
        "PersistenceFailure record(s) were logged ({0}) but none identified "
        "the thermometer reading actually reported ({1})".format(failure_sources, context['sensor'])
    )

@given('the knowledge repository is experiencing storage failures')
def step_given_knowledge_repository_storage_failures(context):
    """Arm the persistence system so the upcoming reading fails to be stored."""
    node_is_online()
    context['simulate_persistence_failure'] = True


@then('that reading should be retrievable from the knowledge repository with the value reported')
def step_then_reading_retrievable_from_knowledge_repository(context):
    step_then_data_persisted(context)

@then('a persistence failure record identifying that reading should be available in the system log')
def step_then_persistence_failure_record_available(context):
    step_then_system_logs_failure(context)
