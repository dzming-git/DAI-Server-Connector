import yaml
from src.config.config import Config
from src.grpc.clients.service_coordinator.service_coordinator_client import ServiceCoordinatorClient
from src.consul import ConsulClient
from typing import Dict, Tuple

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

config = Config()

class SchemeManager:
    def __init__(self, scheme_file: str):
        filename = os.path.basename(scheme_file)
        self.task_id = ''.join(filter(str.isdigit, filename))
        if self.task_id:
            self.task_id = int(self.task_id)
        self.scheme_file = scheme_file
            
        self.consul_client = ConsulClient()
        self.consul_client.consul_ip = config.consul_ip
        self.consul_client.consul_port = config.consul_port
        
        self.service_address: Dict[int, Tuple[str, int]] = {}
        self.clients: Dict[str, ServiceCoordinatorClient] = {}

    def read_scheme(self):
        with open(self.scheme_file, 'r') as file:
            scheme = yaml.safe_load(file)
        return scheme
    
    
    def connect(self) -> None:
        scheme = self.read_scheme()
        modules = scheme['modules'].keys()
        connections = scheme['connections']
        args_global = {}
        
        def find_module(module: str) -> None:
            ip, port = self.consul_client.get_service_address(module)
            self.service_address[module] = (ip, port)
            self.clients[module] = ServiceCoordinatorClient(module, ip, port)
        
        def init_module(module: str) -> None:
            print(f"init {module}: {scheme['modules'][module]}")
            service_coordinator_client = self.clients[module]
            input_args: Dict[str, str] = scheme['modules'][module]['input args']
            if input_args:
                for key, value in input_args.items():
                    if value.startswith('{') and value.endswith('}'):
                        value = args_global[value[1:-1]]
                    input_args[key] = value
            args_output = service_coordinator_client.inform_current_service_info(self.task_id, input_args)
            keys = scheme['modules'][module]['output args']
            if keys:
                for key in keys:
                    if key in args_output:
                        args_global[key] = args_output[key]
        
        def connect_module(connection: Dict[str, str]) -> None:
            print(f"connect {connection['pre']} -> {connection['cur']}\nargs: {connection['args']}")
            service_coordinator_client = self.clients[connection['cur']]
            connection_args: Dict[str, str] = connection['args']
            if connection_args:
                for key, value in connection_args.items():
                    if value.startswith('{') and value.endswith('}'):
                        value = args_global[value[1:-1]]
                    connection_args[key] = value
            service_coordinator_client.inform_previous_service_info(
                task_id=self.task_id,
                pre_service_name=connection['pre'],
                pre_service_ip=self.service_address[connection['pre']][0],
                pre_service_port=self.service_address[connection['pre']][1],
                args=connection_args
            )
        
        def start_module(module: str) -> None:
            print(f'start {module}')
            service_coordinator_client = self.clients[module]
            service_coordinator_client.start(self.task_id)

        
        # 寻找所有模块
        with ThreadPoolExecutor(max_workers=len(modules)) as executor:
            future_to_module = {executor.submit(find_module, module): module for module in modules}
            for future in as_completed(future_to_module):
                future.result()

        # 初始化模块
        with ThreadPoolExecutor(max_workers=len(modules)) as executor:
            future_to_module = {executor.submit(init_module, module): module for module in modules}
            for future in as_completed(future_to_module):
                future.result()

        # 连接模块
        with ThreadPoolExecutor(max_workers=len(connections)) as executor:
            future_to_connection = {executor.submit(connect_module, connection): connection for connection in connections}
            for future in as_completed(future_to_connection):
                future.result()

        # 启动模块
        with ThreadPoolExecutor(max_workers=len(modules)) as executor:
            future_to_module = {executor.submit(start_module, module): module for module in modules}
            for future in as_completed(future_to_module):
                future.result()
    
    def stop(self) -> None:
        scheme = self.read_scheme()
        modules = scheme['modules'].keys()
        
        def stop_module(module: str) -> None:
            print(f"stop {module}: {scheme['modules'][module]}")
            service_coordinator_client = self.clients[module]
            service_coordinator_client.stop(self.task_id)


        # 停止模块
        with ThreadPoolExecutor(max_workers=len(modules)) as executor:
            future_to_module = {executor.submit(stop_module, module): module for module in modules}
            for future in as_completed(future_to_module):
                future.result()
    
schemes_dict : Dict[int, SchemeManager] = {}
