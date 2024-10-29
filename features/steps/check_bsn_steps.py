from behave import given, when, then
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.parsers import parse_topic_data, format_entity
def capture_topic_data(topic):
    if topic == '/TargetSystemData':
        parsed_data = parse_topic_data(topic, line_limit=10)
        return topic, parsed_data, False, None
    parsed_data = parse_topic_data(topic, line_limit=10)
    print(parsed_data)
    high_risk_detected = any(
            float(value) > 10 for value in parsed_data['risk']  # Check each value in each list
        )
    risk_key = f"{topic}_risk"  # Append '_risk' to the data type 
    return topic, parsed_data, high_risk_detected, risk_key

def count_matching_elements(list1, list2):
    matching_elements = set(list1) & set(list2)
    
    # Return the count of matching elements
    return len(matching_elements)
@given('the {topic_name} topic is online')
def step_given_topic_is_online(context, topic_name):
    # Check if /TargetSystemData topic is active
    topic_name = format_entity(topic_name)
    result = subprocess.run(['rostopic', 'list', topic_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    topic_list = result.stdout.decode('utf-8').splitlines()
    assert topic_name in topic_list, f"{topic_name} is not online"


@when('I listen to topics')
def step_when_check_sensors_publishing_data(context):
    context.sensor_data = {}
    context.found_high_risk = []
    context.target_system_data = {}
    # Run all topics in parallel
    with ThreadPoolExecutor() as executor:
        future_to_topic = {
            executor.submit(capture_topic_data, format_entity(row['Topic Name'])): row
            for row in context.table
        }
        for future in as_completed(future_to_topic):
            row = future_to_topic[future]
            topic, parsed_data, is_high_risk, risk_key = future.result()
            #print(f"Topic: {topic}, \nData: {parsed_data}, \nRisk: {is_high_risk},\n Risk Key: {risk_key}")
            if topic == '/TargetSystemData':
                context.target_system_data = parsed_data
            else:
                context.sensor_data[topic] = parsed_data
            
            # Store the risk information with the modified key
            if is_high_risk:
                #print(f"High risk detected in {topic}: {parsed_data}")
                context.found_high_risk.append((risk_key, parsed_data))  # Store as (risk_key, data)
            #print(f"Topic: {topic}, Data: {parsed_data}, Risk: {is_high_risk}, Risk Key: {risk_key}")

    # Ensure at least one high risk was detected
    assert context.found_high_risk, "No high risk detected in sensor topics."



                
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
    print("TARGET SYSTEM DATA: ", context.target_system_data)
    target_system_data = context.target_system_data
    print(f'TARGET sytem data risks: {target_system_data}')
    sensor_data = context.sensor_data
    print(f'SENSOR DATA: {sensor_data}')
    for key, value in risk_key_mapping.items():
    
        print("Target:", key, "Sensor:", value)
        print(f"Target risks: {sensor_data[key]['risk']} Sensor risks: {target_system_data[value]} and patient status: {target_system_data['patient_status']}")
        elements = count_matching_elements(sensor_data[key]['risk'], target_system_data[value])
        assert len(target_system_data['patient_status']) >= elements, "Patient status is not being updated in TargetSystemData."
        assert elements > 0, f"Topics {key} and {value} do not have matching risk data."

    
    
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
    print(f'TARGET sytem data risks: {target_data}')
    print(f'SENSOR DATA: {sensor_data}')
    for key, value in data_key_mapping.items():
    
        print("Target:", key, "Sensor:", value)
        print(f"Target risks: {sensor_data[key]['data']} Sensor data: {target_data[value]}")
        elements = count_matching_elements(sensor_data[key]['data'], target_data[value])
        assert elements > 0, f"Topics {key} and {value} do not have matching risk data."
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