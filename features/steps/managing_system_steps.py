from behave import given, when, then
from utils.parsers import get_rosnode_info
import subprocess
import re

def isNodeg3t1_n(target, topic_list):
  topic_list = topic_list.split(',')
  if target == '/g3t1_n':
    pattern = r'/([^/]+)/'
    matches = re.findall(pattern, topic_list[0])
    print(topic_list)
    node_names = [f'/g3t1_{i}' for i in range(1, 7)]
    topics = [f'/{matches[0]}{name}' for name in node_names] + topic_list[1:]
    return topics, node_names
  else:
    return topic_list, [target]
      
def clean_target(target):
    # Remove anything in parentheses and trailing spaces
    return re.sub(r'\s*\(.*\)$', '', target)

def isNodeCommunicating(node_info, target, topics, bound):
    target_cleaned = clean_target(target)
    print(node_info['connections'])
    return all(
        any(
            conn['topic'] == topic and conn['direction'].startswith(bound)
            for conn in node_info['connections'] if clean_target(conn['to']) == target_cleaned
        )
        for topic in topics
    )

@given('the {node_name} node is online')
def step_given_node_is_online(context, node_name):
    result = subprocess.run(['rosnode', 'info', node_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    context.tested_node = node_name
    context.node_info = get_rosnode_info(result)
    if context.node_info == "unreachable":
        raise Exception(f"Node '{node_name}' is not online or accessible.")
    
    context.outbound_results = []
    context.inbound_results = []

@when('I check if topics {inbound_topic} are inbound and {outbound_topic} are outbound to {target}')
def step_when_check_topics(context, inbound_topic, outbound_topic, target):
    node_info = context.node_info
    outbound_topics, outbound_targets = isNodeg3t1_n(target, outbound_topic)
    inbound_topics, inbound_targets = isNodeg3t1_n(target, inbound_topic)

    try:
        for target in outbound_targets:
            outbound_verified = isNodeCommunicating(node_info, target, outbound_topics, 'outbound')
            print(outbound_verified)
            context.outbound_results.append(outbound_verified)
            # Assert right after checking
            assert outbound_verified, f"Topics {outbound_topics} are not properly outbound to {target} from {context.tested_node}"
        for targetNodes in inbound_targets:
            inbound_verified = isNodeCommunicating(node_info, targetNodes, inbound_topics, 'inbound')
            print(inbound_verified)
            context.inbound_results.append(inbound_verified)
            # Assert right after checking
            assert inbound_verified, f"Topics {inbound_topics} are not properly inbound from {targetNodes} to {context.tested_node}"
    except (KeyError, TypeError, Exception) as e:
        context.outbound_results.append(False)
        print(f"An error occurred while verifying outbound topics: {e}")
        assert False, f"Error occurred while checking outbound topics: {e}"
    

@when('I check if topics {topic_list} are inbound from {target}')
def step_when_check_inbound_topics(context, topic_list, target):
    try:
        print('context: ', context.tested_node)
        print('topic_list: ', topic_list)
        print('target: ', target)
        node_info = context.node_info
        inbound_topics, targets = isNodeg3t1_n(target, topic_list)
        print(inbound_topics)
        print(targets)
        for targetNodes in targets:
            inbound_verified = isNodeCommunicating(node_info, targetNodes, inbound_topics, 'inbound')
            print(inbound_verified)
            context.inbound_results.append(inbound_verified)
            # Assert right after checking
            assert inbound_verified, f"Topics {inbound_topics} are not properly inbound from {targetNodes} to {context.tested_node}"
    
    except (KeyError, TypeError, Exception) as e:
        context.inbound_results.append(False)
        print(f"An error occurred while verifying inbound topics: {e}")
        assert False, f"Error occurred while checking inbound topics: {e}"

@when('I check if topics {topic_list} are outbound to {target}')
def step_when_check_outbound_topics(context, topic_list, target):
    try:
        node_info = context.node_info
        print(topic_list)
        print(target)
        outbound_topics, targets = isNodeg3t1_n(target, topic_list)
        print(f'node targets: {targets}')
        for target in targets:
            print(f'treated topics:{outbound_topics}')
            outbound_verified = isNodeCommunicating(node_info, target, outbound_topics, 'outbound')
            context.outbound_results.append(outbound_verified)
            # Assert right after checking
            assert outbound_verified, f"Topics {outbound_topics} are not properly outbound to {target} from {context.tested_node}"
    
    except (KeyError, TypeError, Exception) as e:
        context.outbound_results.append(False)
        print(f"An error occurred while verifying outbound topics: {e}")
        assert False, f"Error occurred while checking outbound topics: {e}"

@then('{node_name} node is connected appropriately')
def step_then_node_is_connected(context, node_name):
    # Final assertion that ensures all verifications are successful
    assert all(context.inbound_results), f"{node_name} is not receiving all expected inbound topics"
    assert all(context.outbound_results), f"{node_name} is not publishing all expected outbound topics"
