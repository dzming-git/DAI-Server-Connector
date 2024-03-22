from src.app import app
from typing import Dict
from src.scheme.scheme import SchemeManager, schemes_dict
from flask import Response
import time
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
    last_change_time = time.time()  # 记录最近一次image_id改变的时间

    while True:
        assert task_id in image_renderer_clients_dict, f"task id {task_id} not found"
        image_id, buffer = image_renderer_clients_dict[task_id].get_image_buffer_by_image_id(task_id, 0, 640, 360)

        if image_id == 0:
            continue

        # 如果image_id改变了，更新previous_image_id，重置last_change_time为当前时间
        if image_id != previous_image_id:
            previous_image_id = image_id
            last_change_time = time.time()
        else:
            # 如果image_id没有改变，并且自上次变化已经超过1秒，则结束循环
            if time.time() - last_change_time > 1:
                break

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