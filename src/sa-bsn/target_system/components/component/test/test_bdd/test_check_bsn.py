import time

import ros_pytest
from pytest_bdd import scenarios, given, when, then, parsers
from interface_map import SYSTEM_MAP
import rospy
import rosnode
from messages.msg import SensorData
from parsers import process_real_time_topics, capture_topic_data
from asserts import node_is_active, bool_node_is_active
from conftest import _node_topic_info, _capture_sensor_reading, step_when_sensor_reports_new_reading

scenarios("./features/check_bsn.feature")

# High-risk band of every sensor's risk percentage (lowrisk 0,20 / midrisk
# 21,65 / highrisk 66,100 in configurations/target_system/test_g3t1_1.launch).
HIGH_RISK_MIN = 66.0
HIGH_RISK_MAX = 100.0

# How long to wait for the oximeter to report a high-risk reading once the patient is pinned (first transition needs 15s of
# uptime, then the oximeter's moving average refills at 1.3 Hz); normally a no-op, the Outline before it takes longer.
HIGH_RISK_READY_TIMEOUT_S = 60.0

# Capture window once the precondition holds. Explicit `duration` (not the
# default line_limit=10) so the oximeter topic and /TargetSystemData stay open
# over the same wall-clock span - see parsers.parse_topic_data.
HIGH_RISK_CAPTURE_S = 20.0


def _ensure_ros_node():
    # ros_pytest_runner never calls rospy.init_node, and without a node rospy.wait_for_message's subscriber is never
    # registered and silently times out. Same guard as test_BSN-P03.py's.
    if not rospy.core.is_initialized():
        rospy.init_node('bdd_check_bsn', anonymous=True)


def _wait_for_high_risk_oximeter_reading(timeout):
    """Block until the oximeter's own topic reports a risk in the high band.
    Returns (reached, last_risk_seen)."""
    _ensure_ros_node()
    topic = _node_topic_info('the oximeter')['topic']
    deadline = time.time() + timeout
    last_risk = None
    while time.time() < deadline:
        remaining = deadline - time.time()
        try:
            msg = rospy.wait_for_message(topic, SensorData, timeout=max(0.1, min(5.0, remaining)))
        except rospy.ROSException:
            continue
        last_risk = msg.risk
        if HIGH_RISK_MIN <= msg.risk <= HIGH_RISK_MAX:
            return True, last_risk
    return False, last_risk

def count_and_get_matching_elements_with_time(sensor_data, target_system_data, key, value, evaluate):
    matching_count = 0
    matched_data = []

    # Iterate over both lists and check for matching values and time condition
    for i, sensor_risk in enumerate(sensor_data[key][evaluate]):
        for j, target_risk in enumerate(target_system_data[value]):
            print('SENSOR RISK of {}: {} TARGET RISK: {}'.format(key, sensor_risk, target_risk))
            if sensor_risk == target_risk:
                # Parse time strings into floats
                sensor_time = float(sensor_data[key]['%time'][i])
                target_time = float(target_system_data['%time'][j])

                # Round and compare times
                rounded_sensor_time = round(sensor_time, -5) / 1e6
                rounded_target_time = round(target_time, -5) / 1e6

                print('TIME DIFFERENCE in {}: {} - {}'.format(key, rounded_sensor_time, rounded_target_time))

                if abs(rounded_sensor_time - rounded_target_time) < 2000:
                    matching_count += 1
                    matched_data.append({
                        'sensor_risk': sensor_risk,
                        'sensor_time': sensor_time,
                        'target_risk': target_risk,
                        'target_time': target_time
                    })

    return matching_count, matched_data


def step_given_node_is_inactive(context, node):
    node_name = SYSTEM_MAP[node]
    if node_name in rosnode.get_node_names():
        rosnode.kill_nodes([node_name])
    rospy.sleep(.2)

    is_active = bool_node_is_active(node_name)
    assert not is_active, "{} is active".format(node_name)

def bodyhub_not_process(context):
    target_system_data = context['target_system_data']
    assert not target_system_data, "Patient status is unexpectedly updated in TargetSystemData."
    # Check that no risks are present in the target system data
    if target_system_data:
        for key in ['trm_risk', 'ecg_risk', 'oxi_risk', 'abps_risk', 'abpd_risk', 'glc_risk', 'trm_data', 'ecg_data', 'oxi_data', 'abps_data', 'abpd_data', 'glc_data']:
            # Assert that the target system data for risks is empty or doesn't contain any values
            assert not target_system_data[key], "Expected no data for {}, but found: {}".format(key, target_system_data[key])

@when('the oximeter reports a blood oxygenation reading outside its normal range')
def step_when_oximeter_reports_out_of_range(context):
    # The launch file makes this true (see test_check_bsn.launch); here we
    # only wait for it to take effect, so the capture below starts once the
    # oximeter is really publishing high-risk readings.
    reached, last_risk = _wait_for_high_risk_oximeter_reading(HIGH_RISK_READY_TIMEOUT_S)
    topic = _node_topic_info('the oximeter')['topic']
    assert last_risk is not None, (
        "No message at all arrived on {0} within {1}s - the subscription itself "
        "is not working, independent of the patient's risk state."
    ).format(topic, HIGH_RISK_READY_TIMEOUT_S)
    assert reached, (
        "The oximeter kept publishing on {0} but never a high-risk ({1}-{2}) reading "
        "within {3}s (last risk seen: {4}). test_check_bsn.launch pins "
        "oxigenation_State2/3/4 to 0,0,0,0,100 - check those overrides reached the "
        "patient node (`rosparam get /oxigenation_State2`)."
    ).format(topic, HIGH_RISK_MIN, HIGH_RISK_MAX, HIGH_RISK_READY_TIMEOUT_S, last_risk)
    _capture_sensor_reading(context, 'the oximeter', duration=HIGH_RISK_CAPTURE_S)

@then(parsers.parse('the central hub should receive that reading with the value reported by {sensor}'))
@then('the central hub should receive that reading with the value reported by <sensor>')
def step_then_central_hub_receives_reading(context, sensor):
    info = _node_topic_info(sensor)
    count, matched = count_and_get_matching_elements_with_time(
        context['sensor_data'], context['target_system_data'], info['topic'], info['data_key'], 'data'
    )
    assert count > 0, "Topics {} and {} do not have matching data.".format(info['topic'], info['data_key'])

@then('the central hub should classify the patient risk for blood oxygenation as high')
def step_then_central_hub_classifies_high_risk(context):
    info = _node_topic_info('the oximeter')
    count, matched = count_and_get_matching_elements_with_time(
        context['sensor_data'], context['target_system_data'], info['topic'], info['risk_key'], 'risk'
    )
    assert count > 0, "Topics {} and {} do not have matching risk data.".format(info['topic'], info['risk_key'])
    # Was `> 10`, which a low-risk reading (0-20) already satisfies; with the high-risk state now guaranteed
    # (test_check_bsn.launch), check the band the scenario actually names.
    assert any(HIGH_RISK_MIN <= float(m['target_risk']) <= HIGH_RISK_MAX for m in matched), \
        "Central hub did not classify the blood oxygenation reading as high risk ({0}-{1}); matched: {2}".format(
            HIGH_RISK_MIN, HIGH_RISK_MAX, [m['target_risk'] for m in matched])

@given('the central hub is unavailable')
def step_given_central_hub_unavailable(context):
    step_given_node_is_inactive(context, 'the central hub')

@then('no patient risk level should be reported for that reading')
def step_then_no_patient_risk_reported(context):
    bodyhub_not_process(context)
