import threading
import time

import ros_pytest
from pytest_bdd import scenarios, given, when, then, parsers
from test_sensor import SharedSensorTests
from conftest import _node_topic_info, _capture_sensor_reading
from interface_map import SYSTEM_MAP
import rospy
import rosnode
from archlib.msg import AdaptationCommand
from messages.msg import SensorData
from asserts import is_node_receiving_multiple_topics, assert_node_is_online, is_node_publishing_to_topics, check_time_performance, bool_node_is_active

scenarios("./features/BSN-P03.feature")

# The thermometer publishes far slower than /TargetSystemData, so capture both topics over the same wall-clock
# window (not a line count) so the reading and the hub's reaction can land in the same snapshot.
EMERGENCY_CAPTURE_DURATION = 15

# Stand-in for "maximum sampling rate": well above the thermometer's 0.6 Hz baseline (test_g3t1_3.launch), driven as the
# reliability engine does - an AdaptationCommand "freq=" on reconfigure_<node> (Sensor::reconfigure, Sensor.cpp).
MAX_SAMPLING_FREQUENCY_HZ = 20
OVERLOAD_OBSERVATION_WINDOW_S = 2.0
OVERLOAD_MIN_SAMPLES = 6

def _ensure_ros_node():
    if not rospy.core.is_initialized():
        rospy.init_node('bdd_bsn_p03', anonymous=True)

def _drive_sensor_to_max_sampling_rate(node_name, freq=MAX_SAMPLING_FREQUENCY_HZ, repeats=3):
    """Reconfigure a sensor's sampling frequency directly, as the reliability engine does via Sensor::reconfigure
    (Sensor.cpp), so "maximum sampling rate" is an actually induced overload."""
    bare_name = node_name.lstrip('/')
    reconfigure_topics = ['reconfigure_{}'.format(bare_name), 'reconfigure_/{}'.format(bare_name)]
    publishers = [rospy.Publisher(topic, AdaptationCommand, queue_size=10) for topic in reconfigure_topics]
    rospy.sleep(0.2)

    command = AdaptationCommand()
    command.source = 'test'
    command.target = bare_name
    command.action = 'freq={}'.format(freq)

    for _ in range(repeats):
        for publisher in publishers:
            publisher.publish(command)
        rospy.sleep(0.1)

@given(parsers.parse('{sensor} is reporting low-risk readings at its maximum sampling rate'))
def step_given_sensor_overloaded(context, sensor):
    _ensure_ros_node()
    sensor_info = _node_topic_info(sensor)
    node_name = SYSTEM_MAP[sensor]

    _drive_sensor_to_max_sampling_rate(node_name)

    sample_times = []
    lock = threading.Lock()

    def _on_message(_msg):
        with lock:
            sample_times.append(time.time())

    subscriber = rospy.Subscriber(sensor_info['topic'], SensorData, _on_message)
    rospy.sleep(OVERLOAD_OBSERVATION_WINDOW_S)
    subscriber.unregister()

    with lock:
        sample_count = len(sample_times)

    context['overloaded'] = sample_count >= OVERLOAD_MIN_SAMPLES
    assert context['overloaded'], (
        "Expected {} to be streaming at a high sampling rate (>= {} samples in {}s "
        "after reconfiguring it to {} Hz), but only got {} samples".format(
            sensor, OVERLOAD_MIN_SAMPLES, OVERLOAD_OBSERVATION_WINDOW_S, MAX_SAMPLING_FREQUENCY_HZ, sample_count
        )
    )

@when(parsers.parse('{sensor} reports a vital sign reading in the high-risk range'))
def step_when_high_risk_reading_reported(context, sensor):
    assert_node_is_online('/patient_data_service')
    context['sensor_info'] = _node_topic_info(sensor)
    _capture_sensor_reading(context, sensor, duration=EMERGENCY_CAPTURE_DURATION)

@then('the central hub should report an emergency within 250 ms of that reading')
def step_then_central_hub_reports_emergency(context):
    sensor_info = context['sensor_info']
    sensor_topic = sensor_info['topic']
    sensor_payload = context['sensor_data'].get(sensor_topic, {})

    evaluate_key = 'risk' if 'risk' in sensor_payload else 'data'
    target_key = sensor_info['risk_key'] if evaluate_key == 'risk' else sensor_info['data_key']

    performance_check = check_time_performance(
        context['sensor_data'],
        context['target_system_data'],
        sensor_topic,
        target_key,
        evaluate_key,
    )

    assert performance_check, (
        "Central hub failed to report an emergency within 250 ms "
        "(topic='{}', sensor_key='{}', target_key='{}')".format(
            sensor_topic, evaluate_key, target_key
        )
    )
