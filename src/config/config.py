from src.utils import singleton
import yaml

CONFIG_PATH = './.config.yml'

@singleton
class Config:
    def __init__(self):
        #consul
        self.consul_ip: str = ''
        self.consul_port: int = -1
        
        self.load_config()

    def load_config(self):
        with open(CONFIG_PATH, 'r') as f:
            config_data = yaml.safe_load(f)
        consul_data = config_data.get('consul', {})
        self.consul_ip = consul_data.get('ip', '')
        self.consul_port = consul_data.get('port', -1)
