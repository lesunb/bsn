import subprocess
from parsers import get_rosnode_info
import threading
import time
import rosnode

TIMEOUT_SECONDS = 5

class Command(object):
    """A class to execute a command and enforce a timeout."""
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None
        self.stdout = None
        self.stderr = None
        self.returncode = None

    def run(self, timeout=10):
        """Run the command, waiting for a maximum of 'timeout' seconds."""
        
        # Function executed in a separate thread
        def target():
            self.process = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # communicate() blocks until the process finishes
            self.stdout, self.stderr = self.process.communicate()
            self.returncode = self.process.returncode

        thread = threading.Thread(target=target)
        thread.start()
        
        thread.join(timeout)
        
        if thread.is_alive():
            # If the thread is still alive, the timeout expired.
            try:
                # Terminate the process gently, then forcefully kill if needed
                self.process.terminate()
                time.sleep(0.1)
                if thread.is_alive():
                     os.kill(self.process.pid, 9) # Force kill
            except OSError:
                pass # Process already terminated
            
            # Raise the equivalent of the TimeoutExpired exception
            raise Exception("TimeoutExpired") 

        # If we reach here, the thread finished naturally.
        return self.stdout, self.stderr, self.returncode

def kill_node(node_name):
    result = subprocess.Popen(['rosnode', 'kill', node_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = result.communicate()
    assert not bool_node_is_active(node_name), "{} is active".format(node_name)

def is_node_receiving_multiple_topics(node_name, expected_topics):
    """
    Check if a node is receiving data from multiple topics.

    Parameters:
    - node_name (str): The name of the ROS node to check.
    - expected_topics (list): A list of topics that the node is expected to receive data from.

    Returns:
    - bool: True if the node is receiving data from all the expected topics, False otherwise.
    - missing_topics (list): List of topics that are missing if the node is not subscribed to all topics.
    """
    try:
        cmd = ['rosnode', 'info', node_name]
        command = Command(cmd)
        stdout, stderr, returncode = command.run(timeout=TIMEOUT_SECONDS)

        node_info = get_rosnode_info(returncode, stdout, stderr)

        subscriptions = [sub['topic'] for sub in node_info.get('subscriptions', [])]

        inbound_connections = [conn['topic'] for conn in node_info.get('connections', []) if 'inbound' in conn['direction']]

        missing_topics = [topic for topic in expected_topics if topic not in subscriptions and topic not in inbound_connections]
        print('node {}, inbound_connections {} subscriptions: {}'.format(node_name, inbound_connections, subscriptions))
        print('missing_topics: {}'.format(missing_topics))

        if not missing_topics:
            return True, []
        else:
            return False, missing_topics

    except Exception:
        raise AssertionError("Timeout: Failed to check if node {} is receiving data.".format(node_name))
    
def is_node_publishing_to_topics(node_name, expected_topics):
    """
    Check if a node is publishing to multiple expected topics.

    Parameters:
    - node_name (str): The name of the ROS node to check.
    - expected_topics (list): A list of topics that the node is expected to publish to.

    Returns:
    - dict: A dictionary with the expected topics as keys and a tuple as the value. 
            The tuple contains (is_publishing (bool), missing_topics (list)).
    """
    try:
        node_data = subprocess.Popen(['rosnode', 'info', node_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = node_data.communicate()

        node_info = get_rosnode_info(node_data.returncode, stdout, stderr)
        
        publications = [pub['topic'] for pub in node_info.get('publications', [])]
       
        outbound_connections = [conn['topic'] for conn in node_info.get('connections', []) if 'outbound' in conn['direction']]

        missing_topics = [topic for topic in expected_topics if topic not in publications and topic not in outbound_connections]
        print('node {}, outbound_connections {} publications: {}'.format(node_name, outbound_connections, publications))
        print('missing_topics: {}'.format(missing_topics))
        if not missing_topics:
            print('node {} is publishing to all expected topics.'.format(node_name))
            return True, []
        else:
            return False, missing_topics

    except Exception as e:
        print("Error occurred while checking node {}: {}".format(node_name, str(e)))
        raise AssertionError("Timeout: Failed to check if node {} is publishing to topics {}".format(node_name, expected_topics))

def assert_node_is_online(node_name):
    rosnode_list = rosnode.get_node_names()
    assert node_name in rosnode_list, "{} is not online".format(node_name)

def node_is_active(node_names):
    if isinstance(node_names, str):
        node_names = [node_names]
    
    result = subprocess.Popen(['rosnode', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = result.communicate()
    node_list = stdout.decode('utf-8').splitlines()
    for node_name in node_names:
        assert node_name in node_list, "{} is not online. Make sure give the system more time to start up.".format(node_name)

def bool_node_is_active(node_names):
    if isinstance(node_names, str):
        node_names = [node_names]

    result = subprocess.Popen(['rosnode', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = result.communicate()
    node_list = stdout.decode('utf-8').splitlines()
    for node_name in node_names:
        if node_name in node_list:
            return True

    return False

def check_time_performance(sensor_data, target_system_data, key, value, evaluate):
    time_threshold=250000
    # Iterate over both lists and check for matching values and time condition
    for i, sensor_risk in enumerate(sensor_data[key][evaluate]):
        for j, target_risk in enumerate(target_system_data[value]):
            print('SENSOR RISK of {}: {} TARGET RISK: {}'.format(key, sensor_risk, target_risk))
            if sensor_risk == target_risk:
                # Parse time strings into floats
                sensor_time = float(sensor_data[key]['%time'][i]) / 1e3
                target_time = float(target_system_data['%time'][j]) / 1e3

                # Round and compare times
                #rounded_sensor_time = round(sensor_time, -5) / 1e6
                #rounded_target_time = round(target_time, -5) / 1e6
                time_diff = sensor_time - target_time
                print("diff: {}".format(time_diff))
                if time_diff < time_threshold:
                    return True
                print('TIME DIFFERENCE in {}: {} us'.format(key, time_diff))
                
    return False
