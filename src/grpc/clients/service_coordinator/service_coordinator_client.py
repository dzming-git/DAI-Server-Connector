from generated.protos.service_coordinator import service_coordinator_pb2, service_coordinator_pb2_grpc
import grpc
from typing import Dict, List

class ServiceCoordinatorClient:
    class CustomResponse:
        code: int = 0
        message: str = ''
    
    class InformPreviousServiceInfoRequest:
        task_id: int = 0
        pre_service_name: str = ''
        pre_service_ip: str = ''
        pre_service_port: str = ''
        args: Dict[str, str] = {}
    
    class InformPreviousServiceInfoResponse:
        response: 'ServiceCoordinatorClient.CustomResponse' = None
    
    class InformCurrentServiceInfoRequest:
        task_id: int = 0
        args: Dict[str, str] = {}
    
    class InformCurrentServiceInfoResponse:
        response: 'ServiceCoordinatorClient.CustomResponse' = None
        args: Dict[str, str] = {}
    
    class StartRequest:
        task_id: int = 0
    
    class StartResponse:
        response: 'ServiceCoordinatorClient.CustomResponse' = None
    
    class StopRequest:
        task_id: int = 0
    
    class StopResponse:
        response: 'ServiceCoordinatorClient.CustomResponse' = None
    
    def __init__(self, ip:str, port: str):
        self.conn = grpc.insecure_channel(f'{ip}:{port}')
        self.client = service_coordinator_pb2_grpc.CommunicateStub(channel=self.conn)
    
    def informPreviousServiceInfo(self, request: InformPreviousServiceInfoRequest) -> InformPreviousServiceInfoResponse:
        inform_previous_service_info_request = service_coordinator_pb2.InformPreviousServiceInfoRequest()
        inform_previous_service_info_request.taskId = request.task_id
        inform_previous_service_info_request.preServiceName = request.pre_service_name
        inform_previous_service_info_request.preServiceIp = request.pre_service_ip
        inform_previous_service_info_request.preServicePort = request.pre_service_port
        for key, value in request.args.items():
            arg = inform_previous_service_info_request.args.add()
            arg.key = key
            arg.value = value
        
        inform_previous_service_info_response = self.client.informPreviousServiceInfo(inform_previous_service_info_request)
        
        response = ServiceCoordinatorClient.InformPreviousServiceInfoResponse()
        response.response = ServiceCoordinatorClient.CustomResponse()
        response.response.code = inform_previous_service_info_response.response.code
        response.response.message = inform_previous_service_info_response.response.message
        return response
    
    def informCurrentServiceInfo(self, request: InformCurrentServiceInfoRequest) -> InformCurrentServiceInfoResponse:
        inform_current_service_info_request = service_coordinator_pb2.InformCurrentServiceInfoRequest()
        inform_current_service_info_request.taskId = request.task_id
        for key, value in request.args.items():
            arg = inform_current_service_info_request.args.add()
            arg.key = str(key)
            arg.value = str(value)
        
        inform_current_service_info_response = self.client.informCurrentServiceInfo(inform_current_service_info_request)
        
        response = ServiceCoordinatorClient.InformCurrentServiceInfoResponse()
        response.response = ServiceCoordinatorClient.CustomResponse()
        response.response.code = inform_current_service_info_response.response.code
        response.response.message = inform_current_service_info_response.response.message
        for arg in inform_current_service_info_response.args:
            response.args[arg.key] = arg.value
        return response

    def start(self, request: StartRequest) -> StartResponse:
        start_request = service_coordinator_pb2.StartRequest()
        start_request.taskId = request.task_id
        
        start_response = self.client.start(start_request)
        
        response = ServiceCoordinatorClient.StartResponse()
        response.response = ServiceCoordinatorClient.CustomResponse()
        response.response.code = start_response.response.code
        response.response.message = start_response.response.message
        return response
    
    def stop(self, request: StopRequest) -> StopResponse:
        stop_request = service_coordinator_pb2.StopRequest()
        stop_request.taskId = request.task_id
        
        start_response = self.client.stop(stop_request)
        
        response = ServiceCoordinatorClient.StopResponse()
        response.response = ServiceCoordinatorClient.CustomResponse()
        response.response.code = start_response.response.code
        response.response.message = start_response.response.message
        return response
    