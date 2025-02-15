from flask import Flask, render_template, request, send_file
from flaskwebgui import FlaskUI
import os
import json
import requests
from io import BytesIO
from urllib.parse import quote
from routes import create_routes

app = Flask(__name__)
# 创建 DataManager 实例
from utils.data_manager import DataManager

data_manager = DataManager()

# 注册蓝图
create_routes(app, data_manager)


@app.route('/')
@app.route('/introduction')
def introduction():
    """加载项目介绍页面"""
    # 加载联系人列表数据
    if os.path.exists('data/contacts.json'):
        with open('data/contacts.json', 'r', encoding='utf-8') as f:
            contacts = json.load(f)
    else:
        contacts = []

    return render_template('introduction.html', contacts=contacts)


@app.route('/index')
def index():
    """首页"""
    if os.path.exists('data/contacts.json'):
        with open('data/contacts.json', 'r', encoding='utf-8') as f:
            contacts = json.load(f)
    else:
        contacts = []
    return render_template('index.html', contacts=contacts)


@app.route('/proxy/image')
def proxy_image():
    """图片代理"""
    url = request.args.get('url')
    if not url:
        return '缺少图片URL', 400

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://wx.qq.com/'
        }
        response = requests.get(url, headers=headers)
        return send_file(
            BytesIO(response.content),
            mimetype=response.headers.get('content-type', 'image/jpeg')
        )
    except Exception as e:
        print(f"Error proxying image: {str(e)}")
        return '获取图片失败', 500


@app.template_filter('urlencode')
def urlencode_filter(s):
    """URL编码过滤器"""
    if isinstance(s, str):
        return quote(s)
    return ''


if __name__ == '__main__':
    # app.run(debug=True)  # 浏览器
    FlaskUI(app=app, server="flask").run()  # 桌面app
