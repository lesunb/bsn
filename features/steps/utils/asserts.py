import subprocess
from utils.parsers import get_rosnode_info
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
        # Run `rosnode info` command to get information about the node
        node_data = subprocess.run(['rosnode', 'info', node_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        node_info = get_rosnode_info(node_data)

        # Extract the subscriptions (topics the node is subscribed to)
        subscriptions = [sub['topic'] for sub in node_info.get('subscriptions', [])]

        # Extract inbound connections (to check if the node has inbound data from the expected topics)
        inbound_connections = [conn['topic'] for conn in node_info.get('connections', []) if 'inbound' in conn['direction']]

        # Check if all expected topics are in the subscriptions and inbound connections
        missing_topics = [topic for topic in expected_topics if topic not in subscriptions or topic not in inbound_connections]

        if not missing_topics:
            return True, []
        else:
            return False, missing_topics

    except subprocess.TimeoutExpired:
        raise AssertionError(f"Timeout: Failed to check if node {node_name} is receiving data.")
    
def is_node_publishing_to_topics(node_name, expected_topics):
    """
    Check if a node is publishing to multiple expected topics.

    Parameters:
    - node_name (str): The name of the ROS node to check.
    - expected_topics (list): A list of topics that the node is expected to publish to.

    Returns:
    - dict: A dictionary with the expected topics as keys and a tuple as the value. 
            The tuple contains (is_publishing (bool), outbound_connections (list)).
    """
    try:
        # Run `rosnode info` to get the node's information
        node_data = subprocess.run(['rosnode', 'info', node_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        node_info = get_rosnode_info(node_data)
        # Extract the publications (topics the node is publishing to)
        publications = [pub['topic'] for pub in node_info.get('publications', [])]

        # Iterate through the expected topics and check if they are being published
       
        outbound_connections = [conn['topic'] for conn in node_info.get('connections', []) if 'outbound' in conn['direction']]

        missing_topics = [topic for topic in expected_topics if topic not in publications or topic not in outbound_connections]

        if not missing_topics:
            return True, []
        else:
            return False, missing_topics

    except subprocess.TimeoutExpired:
        raise AssertionError(f"Timeout: Failed to check if node {node_name} is publishing to topics {expected_topics}")
