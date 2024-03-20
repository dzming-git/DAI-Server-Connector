from generated.protos.image_renderer import image_renderer_pb2, image_renderer_pb2_grpc
import grpc
from typing import Dict, List
import cv2

from typing import List

class ImageRendererClient:
    class CustomImageRequest:
        def __init__(self, image_id: int = 0, no_image_buffer: bool = False, format: str = '.jpg', params: List[int] = [cv2.IMWRITE_JPEG_QUALITY, 80], expected_w: int = 640, expected_h: int = 360):
            self.image_id = image_id
            self.no_image_buffer = no_image_buffer
            self.format = format
            self.params = params
            self.expected_w = expected_w
            self.expected_h = expected_h
    
    class CustomImageResponse:
        def __init__(self, width: int = 0, height: int = 0, image_id: int = 0, buffer: bytes = b''):
            self.width = width
            self.height = height
            self.image_id = image_id
            self.buffer = buffer
        
    class CustomResponse:
        def __init__(self, code: int = 0, message: str = ''):
            self.code = code
            self.message = message
    
    class GetImageByImageIdRequest:
        def __init__(self, task_id: int = 0, custom_image_request: 'ImageRendererClient.CustomImageRequest' = None):
            self.task_id = task_id
            self.custom_image_request = custom_image_request or ImageRendererClient.CustomImageRequest()
    
    class GetImageByImageIdResponse:
        def __init__(self, response: 'ImageRendererClient.CustomResponse' = None, custom_image_response: 'ImageRendererClient.CustomImageResponse' = None):
            self.response = response or ImageRendererClient.CustomResponse()
            self.custom_image_response = custom_image_response or ImageRendererClient.CustomImageResponse()

    def __init__(self, ip: str, port: int):
        options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024)]
        self.conn = grpc.insecure_channel(f'{ip}:{port}', options=options)
        self.client = image_renderer_pb2_grpc.CommunicateStub(channel=self.conn)
    
    def getImageByImageId(self, request: GetImageByImageIdRequest) -> GetImageByImageIdResponse:
        request_pb2 = image_renderer_pb2.GetImageByImageIdRequest()
        request_pb2.taskId = request.task_id
        request_pb2.imageRequest.imageId = request.custom_image_request.image_id
        request_pb2.imageRequest.noImageBuffer = request.custom_image_request.no_image_buffer
        request_pb2.imageRequest.format = request.custom_image_request.format
        request_pb2.imageRequest.params.extend(request.custom_image_request.params)
        request_pb2.imageRequest.expectedW = request.custom_image_request.expected_w
        request_pb2.imageRequest.expectedH = request.custom_image_request.expected_h

        response_pb2 = self.client.getImageByImageId(request_pb2)
        
        response = ImageRendererClient.GetImageByImageIdResponse()
        response.response = ImageRendererClient.CustomResponse()
        response.response.code = response_pb2.response.code
        response.response.message = response_pb2.response.message
        response.custom_image_response.width = response_pb2.imageResponse.width
        response.custom_image_response.height = response_pb2.imageResponse.height
        response.custom_image_response.image_id = response_pb2.imageResponse.imageId
        response.custom_image_response.buffer = response_pb2.imageResponse.buffer
        return response
