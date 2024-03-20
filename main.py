from src.config.config import Config
from src.app import app

config = Config()

def connect_consul():
    from src.consul import ConsulClient
    consul_client = ConsulClient()
    consul_client.consul_ip = config.consul_ip
    consul_client.consul_port = config.consul_port

if __name__ == '__main__':
    connect_consul()
    app.run(host='0.0.0.0', port=8080)
