from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import subprocess
import time
# from utils.constants import NON_SENSOR_TOPICS

NON_SENSOR_TOPICS = [
        '/collect_energy_status',
        '/persist',
        '/log_energy_status',
        '/TargetSystemData'
]

def format_debug_data(data):
    formatted_output = []
    
    for topic, details in data.items():
        formatted_output.append("\n{0}\nTOPIC: {1}\n{0}".format('='*40, topic))
        
        headers = list(details.keys())
        rows = zip(*details.values())  # Transpose to get row-wise data
        
        # Add headers
        formatted_output.append(" | ".join(headers))
        formatted_output.append("-" * len(formatted_output[-1]))  # Add separator
        
        # Add rows
        for row in rows:
            formatted_output.append(" | ".join(str(value) for value in row))
    
    return "\n".join(formatted_output)


def format_entity(raw_string):
    # Check if any words in the string start with an uppercase letter
    words = raw_string.split()
    if any(word[0].isupper() for word in words):
        # If there are uppercase letters, format in camel case
        formatted_string = ''.join(word.capitalize() for word in words)
    else:
        # Otherwise, format in snake case
        formatted_string = '_'.join(word.lower() for word in words)
    
    # Add a forward slash at the beginning
    return '/{0}'.format(formatted_string)

def capture_topic_data(topic):

    if topic in NON_SENSOR_TOPICS:
        parsed_data = parse_topic_data(topic, line_limit=10)
        
        return topic, parsed_data, False, None
    parsed_data = parse_topic_data(topic, line_limit=10)
    
    high_risk_detected = any(
            float(value) > 10 for value in parsed_data['risk']  # Check each value in each list
        )
    risk_key = "{0}_risk".format(topic)  # Append '_risk' to the data type 
    return topic, parsed_data, high_risk_detected, risk_key

def get_rostopic_sensor_data(returncode, stdout, stderr):
    if returncode != 0:
        raise Exception("Error getting topic data: {0}".format(stderr.decode('utf-8')))

    # Decode the output from bytes to string
    output = stdout.decode('utf-8')

    # Parse the output using regex
    data = {}

    # Match key-value pairs
    header_seq = re.search(r'seq: (\d+)', output)
    header_stamp_secs = re.search(r'secs: (\d+)', output)
    header_stamp_nsecs = re.search(r'nsecs: (\d+)', output)
    data_type = re.search(r'type: "(.*?)"', output)
    data_value = re.search(r'data: ([\d\.]+)', output)
    risk_value = re.search(r'risk: ([\d\.]+)', output)
    batt_value = re.search(r'batt: ([\d\.]+)', output)

    # Fill the parsed data dictionary
    if header_seq:
        data['seq'] = int(header_seq.group(1))
    if header_stamp_secs:
        data['stamp_secs'] = int(header_stamp_secs.group(1))
    if header_stamp_nsecs:
        data['stamp_nsecs'] = int(header_stamp_nsecs.group(1))
    if data_type:
        data['type'] = data_type.group(1)
    if data_value:
        data['data'] = float(data_value.group(1))
    if risk_value:
        data['risk'] = float(risk_value.group(1))
    if batt_value:
        data['batt'] = float(batt_value.group(1))
    
    return data

def get_rosnode_info(returncode, stdout, stderr):
    if returncode != 0:
        raise Exception("Error getting node info: {0}".format(stderr.decode('utf-8')))

    # Decode the output from bytes to string
    output = stdout.decode('utf-8')
    lines = output.splitlines()
    if lines and lines[-1].startswith("cannot contact"):
        return "unreachable"
    # Initialize dictionaries for storing parsed data
    node_info = {
        "publications": [],
        "subscriptions": [],
        "services": [],
        "connections": []
    }

    # Helper function to parse lines with topic and type
    def parse_topic_lines(start_index):
        topics = []
        i = start_index
        while i < len(lines) and lines[i].startswith(' * '):
            line = lines[i].strip().split(' [')
            topic = line[0][2:].strip()  # Remove leading '* '
            type_ = line[1][:-1].strip() if len(line) > 1 else "unknown type"
            topics.append({"topic": topic, "type": type_})
            i += 1
        return topics, i

    # Parse sections
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith('Publications:'):
            # Parse publications starting from the next line
            node_info["publications"], i = parse_topic_lines(i + 1)

        elif line.startswith('Subscriptions:'):
            # Parse subscriptions starting from the next line
            node_info["subscriptions"], i = parse_topic_lines(i + 1)

        elif line.startswith('Services:'):
            # Parse services starting from the next line
            i += 1
            while i < len(lines) and lines[i].startswith(' * '):
                service = lines[i].strip()[2:]  # Remove leading '* '
                node_info["services"].append(service)
                i += 1

        elif line.startswith('Connections:'):
            # Parse connections starting from the next line
            i += 1
            while i < len(lines) and lines[i].startswith(' * topic:'):
                connection = {}
                connection["topic"] = lines[i].split(': ')[1].strip()
                i += 1
                connection["to"] = lines[i].split(': ')[1].strip()
                i += 1
                connection["direction"] = lines[i].split(': ')[1].strip()
                i += 1
                connection["transport"] = lines[i].split(': ')[1].strip()

                # Move to the next line to check for the next connection
                i += 1
                # Add the connection to the list
                node_info["connections"].append(connection)

        else:
            i += 1
    return node_info



import threading
import Queue as queue  # Python 2 uses Queue instead of queue


def enqueue_output(out, output_queue):
    """
    Continuously reads lines from the process output and puts them into a queue.
    This function is intended to be run in a separate thread.
    """
    for line in iter(out.readline, ''):
        output_queue.put(line.strip())
    out.close()

def parse_topic_data(topic, line_limit=10):
    """
    Capture CSV data from a ROS topic using Popen and organize it into a dictionary 
    with headers dynamically set from the first line. Stops reading once line_limit 
    is reached or after the timeout if no data is received.
    """
    process = subprocess.Popen(
        ['rostopic', 'echo', '-p', '--offset', topic],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    output_queue = queue.Queue()
    thread = threading.Thread(target=enqueue_output, args=(process.stdout, output_queue))
    thread.daemon = True
    thread.start()

    parsed_data = None
    headers = None
    start_time = time.time()

    try:
        for i in range(line_limit + 1):
            # Check if we've exceeded the timeout

            try:
                # Try to read a line from the queue with a small timeout
                line = output_queue.get(timeout=13)
                
                # First line contains headers
                if i == 0:
                    headers = [header.replace("field.", "").strip() for header in line.split(",")]
                    parsed_data = {header: [] for header in headers}
                    continue

                # Process data lines if headers are set
                if headers and parsed_data is not None:
                    columns = line.split(",")
                    if len(columns) == len(headers):
                        for header, value in zip(headers, columns):
                            parsed_data[header].append(value.strip())

            except queue.Empty:
                # No new data was found in the queue, continue until timeout
                process.terminate()  # Ensure subprocess terminates
                process.wait() 
                return parsed_data

    except Exception as e:
        print("An error occurred: {0}".format(e))
    finally:
        process.terminate()  # Ensure subprocess terminates
        process.wait()       # Ensure cleanup
    if parsed_data is not None:
        parsed_data = {key: tuple(values) for key, values in parsed_data.items()}
    return parsed_data if parsed_data is not None else {}



def process_real_time_topics(context, capture_topic_data, topics):
    """
    Process topics concurrently and organize results into context.

    Args:
        context: An object containing the table and attributes to store results.
        capture_topic_data: A function to capture and process topic data.
        format_entity: A function to format topic names.
    """
    with ThreadPoolExecutor() as executor:
        # Map futures to rows for tracking
        future_to_topic = {
            executor.submit(capture_topic_data, topic): topic
            for topic in topics
        }

        for future in as_completed(future_to_topic):
            row = future_to_topic[future]
            try:
                topic, parsed_data, is_high_risk, risk_key = future.result()
                if topic == '/TargetSystemData':
                    context['target_system_data'] = parsed_data
                elif topic in NON_SENSOR_TOPICS:
                    print('Non sensor topic data captured for {}: {}'.format(topic, parsed_data))
                    print(topic)
                    print(parsed_data)
                    context['non_sensor'][topic] = parsed_data
                else:
                    context['sensor_data'][topic] = parsed_data

            except Exception as e:
                print("Error processing topic for row {0}: {1}".format(row, e))
