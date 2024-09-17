import re

def get_rostopic_sensor_data(result):
    if result.returncode != 0:
        raise Exception(f"Error getting topic data: {result.stderr.decode('utf-8')}")
    
    # Decode the output from bytes to string
    output = result.stdout.decode('utf-8')
    
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

def get_rosnode_info(result):
    if result.returncode != 0:
        raise Exception(f"Error getting node info: {result.stderr.decode('utf-8')}")

    # Decode the output from bytes to string
    output = result.stdout.decode('utf-8')
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




