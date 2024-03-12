import yaml
from src.config.config import Config
from src.grpc.clients.service_coordinator.service_coordinator_client import ServiceCoordinatorClient
from src.consul import ConsulClient
import random
import numpy as np
from typing import Dict
import os

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
        
        self.service_address = {}
        self.clients = {}

    def read_scheme(self):
        with open(self.scheme_file, 'r') as file:
            scheme = yaml.safe_load(file)
        return scheme
    
    def connect(self):
        scheme = self.read_scheme()
        modules = scheme['modules'].keys()
        output_args = {}
        
        for module in modules:
            ip, port = self.consul_client.get_service_address(module)
            self.service_address[module] = [ip, port]
            self.clients[module] = ServiceCoordinatorClient(ip, port)
        
        for module in modules:
            print(f"{module}: {scheme['modules'][module]}")
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
            if response.response.code != 200:
                return False, response.response.message
            output_arg_keys = scheme['modules'][module]['output args']
            if output_arg_keys:
                for output_arg_key in output_arg_keys:
                    if output_arg_key in response.args:
                        output_args[output_arg_key] = response.args[output_arg_key]
        
        connections = scheme['connections']
        for connection in connections:
            print(connection)
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
            if response.response.code != 200:
                return False, response.response.message
        
        for module in modules:
            print(f'start {module}')
            service_coordinator_client = self.clients[module]
            request = service_coordinator_client.StartRequest()
            request.task_id = self.task_id
            response = service_coordinator_client.start(request)
            if response.response.code != 200:
                return False, response.response.message
            
schemes_dict : Dict[int, SchemeManager] = {}
