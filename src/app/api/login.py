from src.app import app
from flask import request, jsonify, request, make_response
import uuid

@app.route('/login', methods=['POST'])
def login():
    # 获取登录请求的用户名和密码
    username = request.json.get('username')
    password = request.json.get('password')

    # 进行用户名和密码的验证逻辑
    if verify_credentials(username, password):
        # 登录成功，生成一个名为"auth_token"的Cookie，并设置其他相关属性
        response = make_response('Login successful')
        response.set_cookie('auth_token', 'your-auth-token', httponly=True)
        return response
    else:
        # 登录失败，返回错误信息
        return 'Login failed', 401

def verify_credentials(username, password):
    # 进行用户名和密码的验证
    # 在这里你可以根据具体的需求和实现方式进行验证
    # 例如，验证用户名和密码是否匹配数据库中的记录
    if username == 'dzming' and password == '123':
        return True
    else:
        return False

@app.route('/register')
def login_register():
    pass
