import subprocess
import time
#def before_all(context):
#    context.bsn_launch = subprocess.Popen(
#                ['roslaunch', 'bsn.launch'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
#            )
#    time.sleep(30)  # Ensure the system is fully started before proceeding with the test

def before_scenario(context, scenario):
    # Check if the scenario is related to health status
    if 'reduced_system' in scenario.tags:
        print("Starting reduced_system launch file...")
        context.health_status_launch = subprocess.Popen(
            ['roslaunch', 'component', 'sensor_execution.launch'],
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
        time.sleep(50)
    elif 'persistance_system' in scenario.tags:
        context.persistance_system_launch = subprocess.Popen(
            ['roslaunch', 'component', 'persistance_system.launch'],
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
        time.sleep(80)       
        
#    elif 'full_system' in scenario.tags:
#        print("Starting full_system launch file...")
#        context.bsn_launch = subprocess.Popen(
#                ['roslaunch', 'bsn.launch'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
#            )
#        time.sleep(50)
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
    if 'reduced_system' in scenario.tags and hasattr(context, 'health_status_launch'):
        context.health_status_launch.terminate()
        context.health_status_launch.wait()
    elif 'persistance_system' in scenario.tags and hasattr(context, 'persistance_system_launch'):
        context.persistance_system_launch.terminate()
        context.persistance_system_launch.wait()
#    elif 'full_system' in scenario.tags:
#        context.bsn_launch.terminate()
#        context.bsn_launch.wait()

def after_all(context):
    context.bsn_launch.terminate()
    context.bsn_launch.wait()
    if hasattr(context, 'central_hub'):
        context.central_hub.terminate()
        context.central_hub.wait()