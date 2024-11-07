from behave import given, when, then
import subprocess

from utils.parsers import parse_topic_data, format_entity, process_real_time_topics

def node_is_active(node_name):
    result = subprocess.run(['rosnode', 'list', node_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    node_list = result.stdout.decode('utf-8').splitlines()
    return node_name in node_list
def capture_topic_data(topic):
    
    if topic == '/TargetSystemData':
        print('passei aqui no capture topic data')
        parsed_data = parse_topic_data(topic, line_limit=10)
        
        return topic, parsed_data, False, None
    parsed_data = parse_topic_data(topic, line_limit=10)
    
    high_risk_detected = any(
            float(value) > 10 for value in parsed_data['risk']  # Check each value in each list
        )
    risk_key = f"{topic}_risk"  # Append '_risk' to the data type 
    return topic, parsed_data, high_risk_detected, risk_key

def count_and_get_matching_elements_with_time(sensor_data, target_system_data, key, value, evaluate):
    matching_count = 0
    matched_data = []

    # Iterate over both lists and check for matching values and time condition
    for i, sensor_risk in enumerate(sensor_data[key][evaluate]):
        for j, target_risk in enumerate(target_system_data[value]):
            print(f'SENSOR RISK of {key}: {sensor_risk} TARGET RISK: {target_risk}')
            if sensor_risk == target_risk:
                # Parse time strings into floats
                sensor_time = float(sensor_data[key]['%time'][i])
                target_time = float(target_system_data['%time'][j])

                # Round and compare times
                rounded_sensor_time = round(sensor_time, -5) / 1e6
                rounded_target_time = round(target_time, -5) / 1e6

                print(f'TIME DIFFERENCE in {key}: {rounded_sensor_time} - {rounded_target_time}')
                
                if abs(rounded_sensor_time - rounded_target_time) < 2000:
                    matching_count += 1
                    matched_data.append({
                        'sensor_risk': sensor_risk,
                        'sensor_time': sensor_time,
                        'target_risk': target_risk,
                        'target_time': target_time
                    })

    return matching_count, matched_data


@given('the {topic_name} topic is online')
def step_given_topic_is_online(context, topic_name):
    # Check if /TargetSystemData topic is active
    topic_name = format_entity(topic_name)
    result = subprocess.run(['rostopic', 'list', topic_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    topic_list = result.stdout.decode('utf-8').splitlines()
    assert topic_name in topic_list, f"{topic_name} is not online"

@given('the node {node_name} is inactive')
def step_given_node_is_inactive(context, node_name):
    result = subprocess.run(['rosnode', 'kill', node_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert not node_is_active(node_name), f"{node_name} is active"

@when('I listen to topics')
def step_when_check_sensors_publishing_data(context):
    context.sensor_data = {}
    context.found_high_risk = []
    context.target_system_data = {}

    process_real_time_topics(context, capture_topic_data)

                
@then('sensors will process the risks')
def step_then_check_high_risk(context):
    assert any(context.sensor_data.values()), "No risk data found in sensor topics."

    for topic, data in context.sensor_data.items():
        assert 'risk' in data and data['risk'], f"No risk data detected in topic {topic}."

@then("Target System Data will receive the risks from sensors and detect patient's status")
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
    
    target_system_data = context.target_system_data
    
    sensor_data = context.sensor_data
   
    for key, value in risk_key_mapping.items():
    
        print("Target:", key, "Sensor:", value)
        print(f"Target risks: {sensor_data[key]['risk']} Sensor risks: {target_system_data[value]} and patient status: {target_system_data['patient_status']}")
        count, matched = count_and_get_matching_elements_with_time(sensor_data, target_system_data, key, value, 'risk')
        assert target_system_data['patient_status'], f'patient_status is not being provided'
        assert len(target_system_data['patient_status']) >= count, "Patient status is not being updated in TargetSystemData."
        assert count > 0, f"Topics {key} and {value} do not have matching risk data."
        assert all((x.replace('.', '', 1).isdigit() and 0 <= float(x) <= 100) 
                for x in target_system_data['patient_status']), f'patient status is not processing valid risk.'

@then("Target System Data should not receive any risk data or detect patient's status")
def step_then_check_target_system_does_not_receive_risk(context):
    # Print out the target system data for inspection
    print("TARGET SYSTEM DATA (Expected to be empty): ", context.target_system_data)

    target_system_data = context.target_system_data
    
    assert not target_system_data, "Patient status is unexpectedly updated in TargetSystemData."
    # Check that no risks are present in the target system data
    if target_system_data:
        for key in ['trm_risk', 'ecg_risk', 'oxi_risk', 'abps_risk', 'abpd_risk', 'glc_risk']:
            # Assert that the target system data for risks is empty or doesn't contain any values
            assert not target_system_data[key], f"Expected no data for {key}, but found: {target_system_data[key]}"

    
    
    
@then('sensors will process the data')
def step_check_if_sensors_process_data(context):
    assert any(context.sensor_data.values()), "No risk data found in sensor topics."

    for topic, data in context.sensor_data.items():
        assert 'data' in data and data['data'], f"No risk data detected in topic {topic}."
@then('Target System Data will receive the data from sensors')
def step_check_if_TargetSystem_process_data(context):
    data_key_mapping = {
    '/thermometer_data': 'trm_data',
    '/ecg_data': 'ecg_data',
    '/oximeter_data': 'oxi_data',
    '/abps_data': 'abps_data',
    '/abpd_data': 'abpd_data',
    '/glucosemeter_data': 'glc_data',
    }
    print(f'TARGET sytem data: {context.target_system_data}')
    target_data= context.target_system_data
    sensor_data = context.sensor_data

    for key, value in data_key_mapping.items():
    
        print("Target:", key, "Sensor:", value)
        print(f"Target risks: {sensor_data[key]['data']} Sensor data: {target_data[value]}")
        count, matched = count_and_get_matching_elements_with_time(sensor_data, target_data, key, value, 'data')
        assert count > 0, f"Topics {key} and {value} do not have matching risk data."
"""
@then('/TargetSystemData will report a high risk')
def step_then_check_target_system_data_high_risk(context):
    target_system_data = context.target_system_data
    # Assume a threshold for high risk
    high_risk_threshold = 80  # Example threshold for risk
    patient_status_threshold = 15  # Example threshold for patient status

    # Check if patient status is higher when any high risk is found
    if context.found_high_risk:
        print(f"TARGET SYSTEM DATA IN THEN: {target_system_data['data']}")
        assert max(target_system_data['data'].get('patient_status', 0)) > patient_status_threshold, (
            "Patient status has no risk above the threshold"
        )
        # Check if any value in any of the risk lists exceeds the high risk threshold
# Get the list of patient statuses
    patient_status_list = target_system_data['data']['patient_status']

    # Check each risk list for values that exceed the threshold and their corresponding patient status
    for risk_key in ['trm_risk', 'ecg_risk', 'oxi_risk', 'abps_risk', 'abpd_risk', 'glc_risk']:
        risk_list = target_system_data['risks'].get(risk_key, [])
        
        for i, risk_value in enumerate(risk_list):
            # Ensure we have a corresponding patient_status value
            if i < len(patient_status_list):
                patient_status_value = patient_status_list[i]
                
                # Check if the risk value exceeds the high risk threshold
                if risk_value > high_risk_threshold:
                    # Verify that the corresponding patient status is also above the threshold
                    print(f"Risk value: {risk_value}, Sensor: {risk_key}, Patient status: {patient_status_value}")
                    assert patient_status_value > patient_status_threshold, (
                        f"Patient status at position {i} is below the threshold despite a high risk in {risk_key}."
                    )
"""