from src.app import app
from typing import Dict
import grpc
import cv2
import traceback
from src.scheme.scheme import SchemeManager, schemes_dict
from flask import request, jsonify, request, Response
from src.grpc.clients.image_renderer.image_renderer_client import ImageRendererClient

image_renderer_clients_dict : Dict[int, ImageRendererClient] = {}

@app.route('/scheme/start/<int:task_id>')
def scheme_start(task_id: int):
    scheme = None
    try:
        scheme_file = f'schemes/{task_id}.yml'
        scheme = SchemeManager(scheme_file)
        schemes_dict[task_id] = scheme
        scheme.connect()
        video_renderer_address = scheme.service_address['image renderer']
        image_renderer_clients_dict[task_id] = ImageRendererClient(video_renderer_address[0], video_renderer_address[1])
        return 'OK'
    except Exception as e:
        error = '\n'.join([
            f'start task {task_id} error:',
            str(e)
        ])
        try:
            if scheme is not None:
                scheme.stop()
        except Exception as e:
            error = '\n'.join([
                error,
                f'stop task {task_id} error:',
                str(e)
            ])
        return Response(f"<pre>{error}</pre>", mimetype='text/html')

@app.route('/scheme/stop/<int:task_id>')
def scheme_stop(task_id: int):
    try:
        scheme = schemes_dict[task_id]
        scheme.stop()
        if task_id in image_renderer_clients_dict:
            image_renderer_clients_dict.pop(task_id)
        return 'OK'
    except Exception as e:
        error = '\n'.join([
            f'stop task {task_id} error:',
            str(e)
        ])
        return Response(f"<pre>{error}</pre>", mimetype='text/html')


def video_play(task_id: int):
    previous_image_id = None  # 初始化前一个image_id为None
    same_id_count = 0  # 初始化连续相同图像ID的计数器为0
    while 1:
        assert task_id in image_renderer_clients_dict, f"task id {task_id} not found"
        image_id, buffer = image_renderer_clients_dict[task_id].get_image_buffer_by_image_id(task_id, 0, 640, 360)
        if 0 == image_id:
            continue
        # 如果连续两次获取到的image_id相同，则计数器增加，否则重置计数器
        if image_id == previous_image_id:
            same_id_count += 1
            # 如果连续10次获取到的image_id相同，则结束循环
            if same_id_count >= 10:
                break
            continue
        else:
            same_id_count = 0  # 重置计数器
        previous_image_id = image_id  # 更新前一个image_id为当前获取到的image_id
        if not buffer:
            continue
        # 使用生成器（generator）输出图像帧
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')

    scheme_stop(task_id)


@app.route('/scheme/video/<int:task_id>')
def video_feed(task_id: int):
    return Response(video_play(task_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')