import os
import json
import argparse
import re
from datetime import datetime

def parse_rosout_log(file_path):
    logs = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Check for the startup timestamp line
            startup_match = re.match(r'^(\d+\.\d+)\s+(.*)$', line)
            if startup_match and ' ' not in startup_match.group(2):  # crude filter
                try:
                    epoch_time = float(startup_match.group(1))
                    message = startup_match.group(2)
                    logs.append({
                        "timestamp": datetime.utcfromtimestamp(epoch_time).isoformat() + "Z",
                        "log_level": "INFO",
                        "node_name": "startup",
                        "log_message": message,
                        "log_type": "rosout",
                        "source_file": file_path,
                    })
                except:
                    continue
                continue

            # Match standard ROS log lines
            log_match = re.match(
                r'^(?P<time>\d+\.\d+)\s+(?P<level>\w+)\s+(?P<node>/\S+)\s+\[(?P<file>[^\]]+)\]\s+\[topics: (?P<topics>[^\]]+)\]\s+(?P<message>.+)$',
                line
            )
            if log_match:
                try:
                    timestamp = datetime.utcfromtimestamp(float(log_match.group('time'))).isoformat() + "Z"
                    logs.append({
                        "timestamp": timestamp,
                        "log_level": log_match.group('level'),
                        "node_name": log_match.group('node'),
                        "log_message": log_match.group('message'),
                        "source_file": file_path,
                        "log_type": "rosout",
                        "topics": log_match.group('topics'),
                        "source_code": log_match.group('file')
                    })
                except:
                    continue
    return logs

def parse_roslaunch_log(file_path):
    logs = []
    with open(file_path, 'r') as f:
        for line in f:
            match = re.match(
                r"^\[(?P<module>[\w\.]+)\]\[(?P<level>\w+)\] (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}): (?P<message>.*)",
                line,
            )
            if match:
                groups = match.groupdict()
                timestamp_str = groups["timestamp"]
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f').isoformat() + "Z"
                except ValueError:
                    timestamp = None

                logs.append({
                    "timestamp": timestamp,
                    "log_level": groups["level"],
                    "node_name": groups["module"],  # e.g., roslaunch, roslaunch.pmon, etc.
                    "log_message": groups["message"].strip(),
                    "log_type": "roslaunch",
                    "source_file": file_path,
                })
    return logs

def parse_master_log(file_path):
    logs = []
    with open(file_path, 'r') as f:
        for line in f:
            match = re.match(r'\[([^\]]+)\]\[([^\]]+)\]\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}): (.*)', line)
            if match:
                module, log_level, timestamp_str, message = match.groups()
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f').isoformat() + "Z"
                except ValueError:
                    timestamp = None

                logs.append({
                    "timestamp": timestamp,
                    "log_level": log_level,
                    "node_name": module,
                    "log_message": message,
                    "log_type": "master_log",
                    "source_file": file_path,
                })
    return logs


def parse_node_log(file_path):
    logs = []
    node_name = os.path.basename(file_path).split('-')[0]
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Handle /rosout specific entries that may appear in node log files
            if "/rosout" in line:
                rosout_match = re.match(
                    r'\[(?P<time>\d+\.\d+)\]\[(?P<level>\w+)\]\s+(?P<message>.+)', line
                )
                if rosout_match:
                    try:
                        timestamp = datetime.utcfromtimestamp(float(rosout_match.group('time'))).isoformat() + "Z"
                        logs.append({
                            "timestamp": timestamp,
                            "log_level": rosout_match.group('level'),
                            "node_name": "rosout",  # Special tag for rosout messages
                            "log_message": rosout_match.group('message'),
                            "log_type": "rosout_node_log",
                            "source_file": file_path,
                        })
                    except:
                        continue
                continue

            # Standard node log format
            match = re.match(r'\[(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\]\[([^\]]+)\]\s+(?P<message>.+)', line)
            if match:
                timestamp_str, log_level, message = match.groups()
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f').isoformat() + "Z"
                except ValueError:
                    timestamp = None

                logs.append({
                    "timestamp": timestamp,
                    "log_level": log_level,
                    "node_name": node_name,
                    "log_message": message,
                    "log_type": "node_log",
                    "source_file": file_path,
                })
    return logs


def save_parsed_logs(parsed_data, output_dir, name):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{name}.json")
    print(f"[INFO] Saving parsed {name} logs to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(parsed_data, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Parse ROS log files into JSON.")
    parser.add_argument('--roslog-dir', default=os.path.expanduser('~/.ros/log/latest'), help="Path to ROS log session folder.")
    parser.add_argument('--output-dir', default='./parsed_logs', help="Directory to save parsed JSON logs.")
    args = parser.parse_args()

    roslog_dir = args.roslog_dir
    output_dir = args.output_dir

    print(f"[INFO] ROS log dir: {roslog_dir}")
    print(f"[INFO] Output dir: {output_dir}")

    if not os.path.exists(roslog_dir):
        print(f"[ERROR] Log directory does not exist: {roslog_dir}")
        return

    # Parse master.log
    master_log = os.path.join(roslog_dir, 'master.log')
    if os.path.exists(master_log):
        master_data = parse_master_log(master_log)
        save_parsed_logs(master_data, output_dir, 'master')
    else:
        print(f"[WARN] master.log not found.")

    # Parse rosout.log
    rosout_log = os.path.join(roslog_dir, 'rosout.log')
    if os.path.exists(rosout_log):
        rosout_data = parse_rosout_log(rosout_log)
        save_parsed_logs(rosout_data, output_dir, 'rosout')
    else:
        print(f"[WARN] rosout.log not found.")

    # Parse roslaunch-*.log
    for fname in os.listdir(roslog_dir):
        if fname.startswith('roslaunch-') and fname.endswith('.log'):
            roslaunch_data = parse_roslaunch_log(os.path.join(roslog_dir, fname))
            save_parsed_logs(roslaunch_data, output_dir, fname.replace('.log', ''))

    # Parse node logs
    node_logs = []
    for node_log_file in os.listdir(roslog_dir):
        node_log_path = os.path.join(roslog_dir, node_log_file)
        # Check if the file is a .log file, is a regular file, and is not one of the standard log files
        if node_log_file.endswith('.log') and os.path.isfile(node_log_path) and node_log_file not in ['master.log', 'rosout.log'] and not node_log_file.startswith('roslaunch-'):
            node_logs.extend(parse_node_log(node_log_path))
        save_parsed_logs(node_logs, output_dir, 'nodes')

if __name__ == "__main__":
    main()
