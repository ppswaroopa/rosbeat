from elasticsearch import Elasticsearch, helpers
import time

class ElasticsearchIngester:
    def __init__(self, hosts, index, batch_size=500, refresh_interval=5):
        self.es = Elasticsearch(hosts)
        self.index = index
        self.batch_size = batch_size
        self.refresh_interval = refresh_interval

    def ingest_logs(self, logs):
        if not logs:
            print("[INFO] No logs to ingest.")
            return
        
        actions = [
            {
                "_index": self.index,
                "_source": log
            }
            for log in logs
        ]

        print(f"[INFO] Ingesting {len(actions)} logs into Elasticsearch index '{self.index}'...")
        helpers.bulk(self.es, actions)
        print(f"[INFO] Successfully ingested {len(actions)} logs.")

    def continuous_ingest(self, log_generator_func):
        print(f"[INFO] Starting continuous ingestion loop (every {self.refresh_interval}s)...")
        while True:
            logs = log_generator_func()
            self.ingest_logs(logs)
            time.sleep(self.refresh_interval)
