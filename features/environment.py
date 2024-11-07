import subprocess
import time
def before_all(context):
    context.bsn_launch = subprocess.Popen(
                ['roslaunch', 'bsn.launch'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
            )
    time.sleep(30)  # Ensure the system is fully started before proceeding with the test
def after_scenario(context, scenario):
    # Check if scenario tag requires node to be reactivated
    if 'inactive_central_hub' in scenario.tags:
        # Restart the node
        context.central_hub = subprocess.Popen(
            ['roslaunch', 'sa-bsn', 'configurations/target_system/bsn.launch'], 
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
        print("Node reactivated.")
        time.sleep(5)  # Ensure the system is fully restarted before next scenario


def after_all(context):
    context.bsn_launch.terminate()
    context.bsn_launch.wait()
    if hasattr(context, 'central_hub'):
        context.central_hub.terminate()
        context.central_hub.wait()