import os
import argparse
from rosbeat.config import Config
from rosbeat.parser import parse_master_log, parse_rosout_log, parse_roslaunch_log, parse_node_log
from rosbeat.ingester import ElasticsearchIngester

def collect_all_logs(log_dir):
    all_logs = []

    # master.log
    master_log = os.path.join(log_dir, 'master.log')
    if os.path.exists(master_log):
        print("[INFO] Parsing master.log...")
        all_logs.extend(parse_master_log(master_log))

    # rosout.log
    rosout_log = os.path.join(log_dir, 'rosout.log')
    if os.path.exists(rosout_log):
        print("[INFO] Parsing rosout.log...")
        all_logs.extend(parse_rosout_log(rosout_log))

    # roslaunch-*.log
    for fname in os.listdir(log_dir):
        if fname.startswith('roslaunch-') and fname.endswith('.log'):
            print(f"[INFO] Parsing {fname}...")
            all_logs.extend(parse_roslaunch_log(os.path.join(log_dir, fname)))

    # Node logs (per-node logs)
    for fname in os.listdir(log_dir):
        fpath = os.path.join(log_dir, fname)
        if fname.endswith('.log') and fname not in ['master.log', 'rosout.log'] and not fname.startswith('roslaunch-') and os.path.isfile(fpath):
            print(f"[INFO] Parsing node log: {fname}...")
            all_logs.extend(parse_node_log(fpath))

    print(f"[INFO] Total logs collected: {len(all_logs)}")
    return all_logs

def main():
    parser = argparse.ArgumentParser(description="Rosbeat - Ingest ROS log files into Elasticsearch")
    parser.add_argument('--config', default="config.yml", help="Path to configuration YAML file")
    args = parser.parse_args()

    config = Config(args.config)

    ingester = ElasticsearchIngester(
        hosts=config.elasticsearch_hosts,
        index=config.elasticsearch_index,
        batch_size=config.batch_size,
        refresh_interval=config.refresh_interval
    )

    log_dir = config.log_directory
    if not os.path.exists(log_dir):
        print(f"[ERROR] Log directory does not exist: {log_dir}")
        return

    logs = collect_all_logs(log_dir)
    ingester.ingest_logs(logs)

if __name__ == "__main__":
    main()
