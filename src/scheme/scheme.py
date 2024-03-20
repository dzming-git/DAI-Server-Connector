import yaml
from src.config.config import Config
from src.grpc.clients.service_coordinator.service_coordinator_client import ServiceCoordinatorClient
from src.consul import ConsulClient
from typing import Dict, Tuple

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

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
        self.clients = {}

    def read_scheme(self):
        with open(self.scheme_file, 'r') as file:
            scheme = yaml.safe_load(file)
        return scheme
    
    
    def connect(self) -> Tuple[bool, str]:
        scheme = self.read_scheme()
        modules = scheme['modules'].keys()
        connections = scheme['connections']
        output_args = {}
        
        def find_module(module: str) -> Tuple[bool, str]:
            try:
                ip, port = self.consul_client.get_service_address(module)
                self.service_address[module] = (ip, port)
                self.clients[module] = ServiceCoordinatorClient(ip, port)
                return True, 'OK'
            except Exception:
                return False, f'find module {module} failed.\n{traceback.format_exc()}'
        
        def init_module(module: str) -> Tuple[bool, str]:
            try:
                print(f"init {module}: {scheme['modules'][module]}")
                service_coordinator_client = self.clients[module]
                request = service_coordinator_client.InformCurrentServiceInfoRequest()
                request.args.clear()
                request.task_id = self.task_id
                input_args = scheme['modules'][module]['input args']
                if input_args:
                    for key, value in input_args.items():
                        if value.startswith('{') and value.endswith('}'):
                            value = output_args[value[1:-1]]
                        request.args[key] = value
                response = service_coordinator_client.informCurrentServiceInfo(request)
                assert response.response.code == 200, response.response.message
                output_arg_keys = scheme['modules'][module]['output args']
                if output_arg_keys:
                    for output_arg_key in output_arg_keys:
                        if output_arg_key in response.args:
                            output_args[output_arg_key] = response.args[output_arg_key]
                return True, 'OK'
            except Exception:
                return False, f'init module {module} failed.\n{traceback.format_exc()}'
        
        def connect_module(connection: Dict[str, str]) -> Tuple[bool, str]:
            try:
                print(f"connect {connection['pre']} -> {connection['cur']}\nargs: {connection['args']}")
                service_coordinator_client = self.clients[connection['cur']]
                request = service_coordinator_client.InformPreviousServiceInfoRequest()
                request.args.clear()
                request.task_id = self.task_id
                request.pre_service_name = connection['pre']
                request.pre_service_ip = self.service_address[connection['pre']][0]
                request.pre_service_port = self.service_address[connection['pre']][1]
                connection_args = connection['args']
                if connection_args:
                    for key, value in connection_args.items():
                        if value.startswith('{') and value.endswith('}'):
                            value = output_args[value[1:-1]]
                        request.args[key] = value
                response = service_coordinator_client.informPreviousServiceInfo(request)
                assert response.response.code == 200, response.response.message
                return True, 'OK'
            except Exception:
                return False, f"connect module {connection['pre']} -> {connection['cur']} failed.\n{traceback.format_exc()}"
        
        def start_module(module: str) -> Tuple[bool, str]:
            try:
                print(f'start {module}')
                service_coordinator_client = self.clients[module]
                request = service_coordinator_client.StartRequest()
                request.task_id = self.task_id
                response = service_coordinator_client.start(request)
                assert response.response.code == 200, response.response.message
                return True, 'OK'
            except Exception:
                return False, f"connect module {connection['pre']} -> {connection['cur']} failed.\n{traceback.format_exc()}"
        
        # 寻找所有模块
        with ThreadPoolExecutor(max_workers=len(modules)) as executor:
            future_to_module = {executor.submit(find_module, module): module for module in modules}
            for future in as_completed(future_to_module):
                module = future_to_module[future]
                try:
                    success, message = future.result()
                    if not success:
                        return False, f'Finding module {module} failed: {message}'
                except Exception as exc:
                    return False, f'Module {module} find operation generated an exception: {exc}'

        # 初始化模块
        with ThreadPoolExecutor(max_workers=len(modules)) as executor:
            future_to_module = {executor.submit(init_module, module): module for module in modules}
            for future in as_completed(future_to_module):
                module = future_to_module[future]
                try:
                    success, message = future.result()
                    if not success:
                        return False, f'Initializing module {module} failed: {message}'
                except Exception as exc:
                    return False, f'Module {module} initialization generated an exception: {exc}'

        # 连接模块
        with ThreadPoolExecutor(max_workers=len(connections)) as executor:
            future_to_connection = {executor.submit(connect_module, connection): connection for connection in connections}
            for future in as_completed(future_to_connection):
                connection = future_to_connection[future]
                try:
                    success, message = future.result()
                    if not success:
                        return False, f'Connecting {connection["pre"]} -> {connection["cur"]} failed: {message}'
                except Exception as exc:
                    return False, f'Connecting {connection["pre"]} -> {connection["cur"]} generated an exception: {exc}'

        # 启动模块
        with ThreadPoolExecutor(max_workers=len(modules)) as executor:
            future_to_module = {executor.submit(start_module, module): module for module in modules}
            for future in as_completed(future_to_module):
                module = future_to_module[future]
                try:
                    success, message = future.result()
                    if not success:
                        return False, f'Starting module {module} failed: {message}'
                except Exception as exc:
                    return False, f'Module {module} start operation generated an exception: {exc}'

        return True, 'OK'
    
    def stop(self) -> Tuple[bool, str]:
        scheme = self.read_scheme()
        modules = scheme['modules'].keys()
        
        def stop_module(module: str) -> Tuple[bool, str]:
            try:
                print(f"stop {module}: {scheme['modules'][module]}")
                service_coordinator_client = self.clients[module]
                request = service_coordinator_client.StopRequest()
                request.task_id = self.task_id
                response = service_coordinator_client.stop(request)
                assert response.response.code == 200, response.response.message
                return True, 'OK'
            except Exception:
                return False, f"stop module {module} failed.\n{traceback.format_exc()}"

        # 停止模块
        with ThreadPoolExecutor(max_workers=len(modules)) as executor:
            future_to_module = {executor.submit(stop_module, module): module for module in modules}
            for future in as_completed(future_to_module):
                module = future_to_module[future]
                try:
                    success, message = future.result()
                    if not success:
                        return False, f'Stoping module {module} failed: {message}'
                except Exception as exc:
                    return False, f'Module {module} stop operation generated an exception: {exc}'

        return True, 'OK'
    
schemes_dict : Dict[int, SchemeManager] = {}
