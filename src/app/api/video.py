from src.app import app
from typing import Dict
import grpc
import cv2
import traceback
from src.scheme.scheme import SchemeManager, schemes_dict
from flask import request, jsonify, request, Response
from generated.protos.image_renderer import image_renderer_pb2, image_renderer_pb2_grpc

QUALITY = 80
W = 640
H = 360

image_renderer_clients_dict : Dict[int, image_renderer_pb2_grpc.CommunicateStub] = {}

@app.route('/scheme/start/<int:task_id>')
def scheme_start(task_id: int):
    scheme = None
    try:
        scheme_file = f'schemes/{task_id}.yml'
        scheme = SchemeManager(scheme_file)
        schemes_dict[task_id] = scheme
        connect_success, msg = scheme.connect()
        assert connect_success, msg
        video_renderer_address = scheme.service_address['image renderer']
        options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024)]
        image_renderer_conn = grpc.insecure_channel(f'{video_renderer_address[0]}:{video_renderer_address[1]}', options=options)
        image_renderer_clients_dict[task_id] = image_renderer_pb2_grpc.CommunicateStub(channel=image_renderer_conn)
        return 'OK'
    except:
        if scheme is not None:
            scheme.stop()
        return traceback.format_exc()

@app.route('/scheme/stop/<int:task_id>')
def scheme_stop(task_id: int):
    try:
        scheme = schemes_dict[task_id]
        scheme.stop()
        if task_id in image_renderer_clients_dict:
            image_renderer_clients_dict.pop(task_id)
        return 'OK'
    except:
        return traceback.format_exc()

def video_play(task_id):
    while 1:
        get_image_by_image_id_request = image_renderer_pb2.GetImageByImageIdRequest()
        get_image_by_image_id_request.taskId = int(task_id)
        get_image_by_image_id_request.imageRequest.format = '.jpg'
        get_image_by_image_id_request.imageRequest.expectedW = W
        get_image_by_image_id_request.imageRequest.expectedH = H
        get_image_by_image_id_request.imageRequest.params.extend([cv2.IMWRITE_JPEG_QUALITY, QUALITY])
        get_image_by_image_id_request.imageRequest.imageId = 0  # 最新
        
        assert task_id in image_renderer_clients_dict, f"task id {task_id} not found"
        get_image_by_image_id_response = image_renderer_clients_dict[task_id].getImageByImageId(get_image_by_image_id_request)
        response = get_image_by_image_id_response.response
        if 200 != response.code:
            print(f'{response.code}: {response.message}')
            continue
        image_id = get_image_by_image_id_response.imageResponse.imageId
        buffer = get_image_by_image_id_response.imageResponse.buffer
        if not buffer:
            continue
        # 使用生成器（generator）输出图像帧
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')

@app.route('/scheme/video/<int:task_id>')
def video_feed(task_id):
    return Response(video_play(task_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')