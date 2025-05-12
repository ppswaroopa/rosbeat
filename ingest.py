from elasticsearch import Elasticsearch, helpers
import json
import os
import time

# Specify the scheme (http) and host details
es = Elasticsearch([{'host': 'elasticsearch', 'port': 9200, 'scheme': 'http'}])

# Check if Elasticsearch is available
def check_es_connection():
    try:
        if es.ping():
            print("[INFO] Elasticsearch connection successful!")
        else:
            print("[ERROR] Elasticsearch connection failed!")
            exit(1)
    except Exception as e:
        print(f"[ERROR] Elasticsearch connection error: {e}")
        exit(1)

def bulk_index_logs(log_dir):
    for log_file in os.listdir(log_dir):
        if log_file.endswith(".json"):
            log_path = os.path.join(log_dir, log_file)
            try:
                with open(log_path, 'r') as f:
                    logs = json.load(f)
                    actions = []
                    for entry in logs:
                        action = {
                            "_op_type": "index",
                            "_index": "ros_logs",
                            "_source": entry
                        }
                        actions.append(action)

                    # Bulk indexing into Elasticsearch
                    success, failed = helpers.bulk(es, actions)
                    if success:
                        print(f"[INFO] Successfully ingested {log_file} into Elasticsearch.")
                    else:
                        print(f"[WARN] Failed to ingest some entries from {log_file}.")
            except Exception as e:
                print(f"[ERROR] Error processing file {log_file}: {e}")

if __name__ == "__main__":
    check_es_connection()  # Ensure Elasticsearch is reachable
    bulk_index_logs("/root/rosbeat/parsed_logs")
