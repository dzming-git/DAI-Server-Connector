from src.config.config import Config
from src.grpc.clients.service_coordinator.service_coordinator_client import ServiceCoordinatorClient
from src.consul import ConsulClient
from src.consul import ServiceInfo
from src.utils import get_local_ip_address
from src.scheme.scheme import SchemeManager
import time
from src.app import app

config = Config()
consul_client = ConsulClient()
consul_client.consul_ip = config.consul_ip
consul_client.consul_port = config.consul_port

def connect_consul():
    host = get_local_ip_address()
    service_name = config.service_name
    service_port = config.service_port
    service_info = ServiceInfo()
    service_info.service_ip = host
    service_info.service_port = service_port
    service_info.service_name = service_name

    for weight_file in config.weights_map:
        weight_info = config.weights_map[weight_file]
        service_info.service_id = f'{service_name}-{weight_file}-{host}-{service_port}'
        service_info.service_tags = config.service_tags
        for label in weight_info.labels:
            service_info.service_tags.append(f'label:{label}')

        consul_client.register_service(service_info)

if __name__ == '__main__':
    connect_consul()
    app.run(host='0.0.0.0', port=8080)
