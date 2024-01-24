
from src.app import app
from flask import jsonify, request
import os


@app.route('/file/list', methods=['GET'])
def get_file_list():
    # 在这里编写获取文件列表的逻辑
    # 假设你已经获取到文件列表，存储在files变量中
    files = os.listdir('schemes/')

    # 返回文件列表作为JSON响应
    return jsonify({'files': files})

@app.route('/file/content', methods=['GET'])
def get_file_content():
    filename = request.args.get('filename') # 获取查询参数中的文件名
    file_path = os.path.join('schemes', filename) # 替换为你的文件路径

    try:
        with open(file_path, 'r') as file:
            content = file.read()
            # 返回文件内容作为JSON响应
            return jsonify({'content': content})
    except FileNotFoundError:
        return jsonify({'error': '文件未找到'})
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/file/update', methods=['POST'])
def update_data():
    data = request.get_json()
    
    # 处理编辑后的数据
    # ...

    # 返回响应
    return jsonify({'message': 'Data updated successfully'})

@app.route('/data')
def get_data():
    nodes = [
        {"id": 0, "nodeName": "A", "shape": "rect"},
        {"id": 1, "nodeName": "B", "shape": "diamond"},
        {"id": 2, "nodeName": "C", "shape": "rect"},
        {"id": 3, "nodeName": "D", "shape": "rect"},
        {"id": 4, "nodeName": "E", "shape": "rect"},
        {"id": 5, "nodeName": "F", "shape": "rect"}
    ]
    edges = [
        {"start": 0, "end": 1, "label": "哈哈\naaa"},
        {"start": 1, "end": 2, "label": ""},
        {"start": 1, "end": 3, "label": ""},
        {"start": 2, "end": 4, "label": ""},
        {"start": 3, "end": 5, "label": ""},
        {"start": 4, "end": 5, "label": ""}
    ]
    data = {"nodes": nodes, "edges": edges}
    return jsonify(data)