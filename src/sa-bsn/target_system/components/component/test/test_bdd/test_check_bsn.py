import ros_pytest
from pytest_bdd import scenarios, given, when, then, parsers
from conftest import FULL_SYSTEM
import rospy
import rosnode
from parsers import parse_topic_data, format_entity, process_real_time_topics, capture_topic_data, format_debug_data
from asserts import node_is_active, bool_node_is_active
import subprocess

scenarios("./features/check_bsn.feature")

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
   

@given(parsers.parse('the {topic_name} topic is online'))
def step_given_topic_is_online(context, topic_name):
    topic_name = format_entity(topic_name)
    result = subprocess.run(['rostopic', 'list', topic_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    topic_list = result.stdout.decode('utf-8').splitlines()
    assert topic_name in topic_list, "{} is not online".format(topic_name)

@given('that all sensors and central hub nodes are online')
def step_given_full_system_nodes_online(context):
    node_is_active(FULL_SYSTEM)  

@given('that all sensors are and online Central hub is inactive')
def step_given_full_system_nodes_online(context):
    node_is_active(FULL_SYSTEM[:-1])  
    if '/g4t1' in rosnode.get_node_names():
        rosnode.kill_nodes(['/g4t1'])
    rospy.sleep(.2)


@given(parsers.parse('{node_name} is inactive'))
def step_given_node_is_inactive(context, node_name):
    is_active = bool_node_is_active(node_name)
    assert not is_active, "{} is active".format(node_name)

@when('I listen to sensors data')
def step_when_check_sensors_publishing_data(context):
    
    context['sensor_data'] = {}
    context['found_high_risk'] = []
    context['target_system_data'] = {}
    
    topics = [
        "/thermometer_data",
        "/ecg_data",
        "/oximeter_data",
        "/abps_data",
        "/abpd_data",
        "/glucosemeter_data",
        "/TargetSystemData"
    ]

    process_real_time_topics(context, capture_topic_data, topics)

@when('I listen to ecg and thermometer data')
def step_when_check_sensors_publishing_data(context):

    context['sensor_data'] = {}
    context['found_high_risk'] = []
    context['target_system_data'] = {}

    topics = [
        "/thermometer_data",
        "/ecg_data",
        "/TargetSystemData"
    ]

    process_real_time_topics(context, capture_topic_data, topics)

                
@then('sensors will process the risks')
def step_then_check_high_risk(context):
    assert any(context['sensor_data'].values()), "No risk data found in sensor topics."
    print('Sensor data: {}'.format(format_debug_data(context['sensor_data'])))
    
    for topic, data in context['sensor_data'].items():
        assert 'risk' in data and data['risk'], "No risk data detected in topic {}".format(topic)

@then("Central hub will process the risk")
def step_then_check_target_system_receives_risk(context):
    #print(f'TargetSystemData is receiving the risk data from sensors: {context.target_system_data}')
    risk_key_mapping = {
    '/thermometer_data': 'trm_risk',
    '/ecg_data': 'ecg_risk',
    '/oximeter_data': 'oxi_risk',
    '/abps_data': 'abps_risk',
    '/abpd_data': 'abpd_risk',
    '/glucosemeter_data': 'glc_risk',
    }

    target_system_data = context['target_system_data']

    sensor_data = context['sensor_data']

    for key, value in risk_key_mapping.items():
    
        print("Target:", key, "Sensor:", value)
        print("Target risks: {} Sensor risks: {} and patient status: {}".format(sensor_data[key]['risk'], target_system_data[value], target_system_data['patient_status']))
        count, matched = count_and_get_matching_elements_with_time(sensor_data, target_system_data, key, value, 'risk')
        assert target_system_data['patient_status'], 'patient_status is not being provided'
        assert len(target_system_data['patient_status']) >= count, "Patient status is not being updated in TargetSystemData."
        assert count > 0, "Topics {} and {} do not have matching risk data.".format(key, value)
        assert all((x.replace('.', '', 1).isdigit() and 0 <= float(x) <= 100) 
                for x in target_system_data['patient_status']), 'patient status is not processing valid risk.'

@then("Central hub will not process the risk")
def step_then_check_target_system_does_not_receive_risk(context):
    target_system_data = context['target_system_data']
    assert not target_system_data, "Patient status is unexpectedly updated in TargetSystemData."
    # Check that no risks are present in the target system data
    if target_system_data:
        for key in ['trm_risk', 'ecg_risk', 'oxi_risk', 'abps_risk', 'abpd_risk', 'glc_risk']:
            # Assert that the target system data for risks is empty or doesn't contain any values
            assert not target_system_data[key], "Expected no data for {}, but found: {}".format(key, target_system_data[key])

@then("Central hub will not process the data")
def step_then_check_target_system_does_not_receive_risk(context):
    target_system_data = context['target_system_data']
    
    assert not target_system_data, "Patient status is unexpectedly updated in TargetSystemData."
    # Check that no risks are present in the target system data
    if target_system_data:
        for key in ['trm_data', 'ecg_data', 'oxi_data', 'abps_data', 'abpd_data', 'glc_data']:
            # Assert that the target system data for risks is empty or doesn't contain any values
            assert not target_system_data[key], "Expected no data for {}, but found: {}".format(key, target_system_data[key])    
    
@then('Sensors will process the data')
def step_check_if_sensors_process_data(context):
    assert any(context['sensor_data'].values()), "No risk data found in sensor topics."

    for topic, data in context['sensor_data'].items():
        assert 'data' in data and data['data'], "No risk data detected in topic {}".format(topic)
@then('Central hub will receive data from sensors')
def step_check_if_TargetSystem_process_data(context):
    data_key_mapping = {
    '/thermometer_data': 'trm_data',
    '/ecg_data': 'ecg_data',
    '/oximeter_data': 'oxi_data',
    '/abps_data': 'abps_data',
    '/abpd_data': 'abpd_data',
    '/glucosemeter_data': 'glc_data',
    }
    
    target_data= context['target_system_data']
    sensor_data = context['sensor_data']

    for key, value in data_key_mapping.items():
    

        count, matched = count_and_get_matching_elements_with_time(sensor_data, target_data, key, value, 'data')
        assert count > 0, "Topics {} and {} do not have matching risk data.".format(key, value)