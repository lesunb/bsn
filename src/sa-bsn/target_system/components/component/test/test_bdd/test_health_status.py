import ros_pytest
from pytest_bdd import scenarios, given, when, then, parsers
import rospy
import rosnode

scenarios("./features/health_status.feature")

@then('a patient health status derived from that reading should be available')
def step_then_patient_health_status_available(context):
    assert len(set(context['target_system_data']['patient_status'])) > 1, "status has not changed. Patient Status: {}".format(context['target_system_data']['patient_status'])

@given('the central hub is unable to process incoming readings')
def step_given_central_hub_unable_to_process(context):
    rospy.sleep(2)

    if '/g4t1' in rosnode.get_node_names():
        rosnode.kill_nodes(['/g4t1'])
    rospy.sleep(2)

@then('no new patient health status should be produced for that reading')
def step_then_no_new_health_status_produced(context):
    target_data = context.get('target_system_data') or {}
    patient_status = target_data.get('patient_status') or []

    assert len(set(patient_status)) == 0, "status has changed, but no new patient health status should be produced"
