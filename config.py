import os
from pathlib import Path


class Config:
    """应用配置类"""
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    DEBUG = os.environ.get('FLASK_ENV') == 'development'

    # 数据目录配置
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / 'data'
    CONTACTS_DIR = DATA_DIR / 'contacts'

    # 确保必要的目录存在
    DATA_DIR.mkdir(exist_ok=True)
    CONTACTS_DIR.mkdir(exist_ok=True)

    # 应用配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大上传文件大小：16MB
    ALLOWED_EXTENSIONS = {'csv', 'json'}  # 允许上传的文件类型

    # API配置
    API_TIMEOUT = 30  # API请求超时时间（秒）
