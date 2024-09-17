from behave import given, when, then
import subprocess
import time
@given('the ROS environment is working')
def step_ros_up(context):
    # Launch ROS or check if it is already running
    try:
        result = subprocess.run(['rosnode', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert result.returncode == 0, "ROS is not running." + result.stderr.decode('utf-8')
    except subprocess.CalledProcessError as e:
        raise AssertionError(f"Failed to check ROS environment: {e}")

@when('I list the available ROS services')
def step_list_ros_services(context):
    result = subprocess.run(['rosservice', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    context.services = result.stdout.decode('utf-8').splitlines()
    assert len(context.services) > 0, "No ROS services found."
    
@then('the EffectorRegister service should be listed')
def step_check_effector_register(context):
    assert '/EffectorRegister' in context.services, "EffectorRegister service is not available."
