from flask import Flask, request, redirect

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 禁止中文转义

protected_routes = ['/user/info']

def verify_token(cookie):
    return True
    # if cookie == 'your-auth-token':
    #     return True
    # return False

# 在请求之前进行令牌验证
@app.before_request
def cookie_verification():
    cookie = request.cookies.get('auth_token')

    if not verify_token(cookie):
        # 验证失败，返回错误或重定向到登录页面
        return redirect('/login')


from src.app.api import *
