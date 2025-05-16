import yaml
import os

class Config:
    def __init__(self, config_file="config.yml"):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file {config_file} not found.")
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)

    def get(self, key, default=None):
        return self.config.get(key, default)

    @property
    def log_directory(self):
        return os.path.expanduser(self.get('log_directory', '~/.ros/log/latest'))

    @property
    def output_directory(self):
        return os.path.expanduser(self.get('output_directory', './parsed_logs'))

    @property
    def elasticsearch_hosts(self):
        return self.get('elasticsearch', {}).get('hosts', ['http://localhost:9200'])

    @property
    def elasticsearch_index(self):
        return self.get('elasticsearch', {}).get('index', 'rosbeat-logs')

    @property
    def batch_size(self):
        return self.get('elasticsearch', {}).get('batch_size', 500)

    @property
    def refresh_interval(self):
        return self.get('elasticsearch', {}).get('refresh_interval', 5)
