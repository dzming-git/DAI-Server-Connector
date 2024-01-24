from src.app import app
from flask import request, jsonify, request

@app.route("/user/info", methods=["GET", "POST"])
def user_info():
    """
    获取当前用户信息
    :return:
    """
    return jsonify({
        "code": 0,
        "data": {
            "id": "1",
            "userName": "admin",
            "realName": "张三",
            "userType": 1
        }
    })
