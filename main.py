from src.config.config import Config
import time
from src.app import app

config = Config()


def connect_consul():
    from src.consul import ConsulClient
    from src.consul import ServiceInfo
    from src.utils import get_local_ip_address

    consul_client = ConsulClient()
    consul_client.consul_ip = config.consul_ip
    consul_client.consul_port = config.consul_port
    host = get_local_ip_address()
    service_name = config.service_name
    service_port = config.service_port
    service_info = ServiceInfo()
    service_info.service_ip = host
    service_info.service_port = service_port
    service_info.service_name = service_name
    service_info.service_id = f'{service_name}-{host}-{service_port}'
    service_info.service_tags = config.service_tags
    consul_client.register_service(service_info)

if __name__ == '__main__':
    connect_consul()
    app.run(host='0.0.0.0', port=8080)
