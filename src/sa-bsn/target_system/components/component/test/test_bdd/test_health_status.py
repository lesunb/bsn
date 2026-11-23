import ros_pytest
from pytest_bdd import scenarios, given, when, then, parsers
import rospy
import rosnode
from health_status_oracle import assert_health_observation

scenarios("./features/health_status.feature")

@then('valid and varying patient health status values should be observed')
def step_then_patient_health_status_available(context):
    assert_health_observation(
        context['sensor_data']['/thermometer_data'].get('data', []),
        context['target_system_data'].get('patient_status', []))

@given('the central hub is unable to process incoming readings')
def step_given_central_hub_unable_to_process(context):
    rospy.sleep(2)

    if '/g4t1' in rosnode.get_node_names():
        rosnode.kill_nodes(['/g4t1'])
    rospy.sleep(2)

@then('no patient health status should be observed while thermometer readings continue')
def step_then_no_new_health_status_produced(context):
    # Direct indexing prevents a missing capture from masquerading as silence.
    assert_health_observation(
        context['sensor_data']['/thermometer_data'].get('data', []),
        context['target_system_data'].get('patient_status', []),
        expect_output=False)
