from behave import given, when, then
import subprocess
from utils.parsers import get_rostopic_sensor_data
from utils.asserts import is_node_receiving_multiple_topics, is_node_publishing_to_topics
@given('the ROS environment is on')
def step_ros_up(context):
    # Launch ROS or check if it is already running
    try:
        result = subprocess.run(['rosnode', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        context.sensor_nodes = ['/g3t1_1', '/g3t1_2', '/g3t1_3', '/g3t1_4','/g3t1_5','/g3t1_6']
        context.sensor_topics = ['/oximeter_data', '/ecg_data', '/thermometer_data','/abps_data', '/abpd_data', '/glucosemeter_data']
        context.node_topic_map = {
        '/g3t1_1': ['/oximeter_data'],
        '/g3t1_2': ['/ecg_data'],
        '/g3t1_3': ['/thermometer_data'],
        '/g3t1_4': ['/abps_data'],
        '/g3t1_5': ['/abpd_data'],
        '/g3t1_6': ['/glucosemeter_data'],
        }
        assert result.returncode == 0, "ROS is not running." + result.stderr.decode('utf-8')
    except subprocess.CalledProcessError as e:
        raise AssertionError(f"Failed to check ROS environment: {e}")

@when('I check if the sensors are publishing data')
def step_check_sensors_publishing(context):
    context.node_data = {}

    # context.node_topic_map maps nodes to a list of topics they should be publishing to
    for node, expected_topics in context.node_topic_map.items():
        is_publishing, missing_topics = is_node_publishing_to_topics(node, expected_topics)
        assert is_publishing, f"{node} is missing data from these topics: {missing_topics}"


@when('I check if respective topics have data')
def step_check_topics_have_data(context):
    context.sensor_data = {}
    for topic in context.sensor_topics:
        try:
            topic_data = subprocess.run(['rostopic', 'echo', topic, '-n', '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=7)
            context.sensor_data[topic] = get_rostopic_sensor_data(topic_data)
            assert context.sensor_data[topic]['data'], f"No data published on topic {topic}"
        except subprocess.TimeoutExpired:
            raise AssertionError(f"Timeout: No data published on topic {topic}")

@then('/g4t1 should receive data')
def step_check_g4t1_receiving_data(context):
    node_name = '/g4t1'
    context.sensor_topics
    is_receiving, missing_topics = is_node_receiving_multiple_topics('/g4t1', context.sensor_topics)

    assert is_receiving, f"{node_name} is missing data from these topics: {missing_topics}"


@when('the /g4t1 node is publishing data')
def step_g4t1_publishing_data(context):
    is_publishing, missing_topics = is_node_publishing_to_topics('g4t1', ['/TargetSystemData'])
    assert is_publishing, "/g4t1 is not publishing to /TargetSystemData"

@when('respective topics have data')
def step_respective_topics_have_data(context):
    context.target_system_data = {}
    topic = '/TargetSystemData'
    try:
        topic_data = subprocess.run(['rostopic', 'echo', topic, '-n', '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        context.target_system_data[topic] = get_rostopic_sensor_data(topic_data)
        assert context.target_system_data[topic]['data'], f"No data published on topic {topic}"
    except subprocess.TimeoutExpired:
        raise AssertionError(f"Timeout: No data published on topic {topic}")
    

@then('the /data_access node should received it')
def step_data_access_should_receive(context):
    is_receiving, missing_topics = is_node_receiving_multiple_topics('/data_access', ['/TargetSystemData']), "/data_access is not receiving data"
    assert is_receiving, f"{'/data_access'} is missing data from these topics: {missing_topics}"

