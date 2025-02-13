from pathlib import Path
from typing import Dict, Optional, Any
import json
from datetime import datetime, date
import numpy as np
import pandas as pd
from dataclasses import dataclass


@dataclass
class DataPaths:
    """数据路径配置"""
    BASE_DIR: Path = Path('data')
    CONTACTS_DIR: Path = BASE_DIR / 'contacts'
    CONTACTS_FILE: Path = BASE_DIR / 'contacts.json'


class DateTimeEncoder(json.JSONEncoder):
    """处理日期时间的JSON编码器"""

    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        if pd.isna(obj):
            return None
        return super().default(obj)


class DataManager:
    def __init__(self):
        """初始化数据管理器"""
        self.paths = DataPaths()
        self.paths.BASE_DIR.mkdir(exist_ok=True)
        self.paths.CONTACTS_DIR.mkdir(exist_ok=True)

    def _get_contact_dir(self, contact_id: int) -> Path:
        """获取联系人数据目录"""
        return self.paths.CONTACTS_DIR / str(contact_id)

    def init_contact_directory(self, contact_id: int) -> None:
        """初始化联系人数据目录结构"""
        contact_dir = self._get_contact_dir(contact_id)
        for subdir in ['basic', 'interactive', 'semantic']:
            (contact_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _save_json(self, path: Path, data: Any) -> None:
        """保存JSON数据"""
        with path.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)

    def _load_json(self, path: Path) -> Optional[Dict]:
        """加载JSON数据"""
        if path.exists():
            with path.open('r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def save_raw_data(self, contact_id: int, chat_data: Dict) -> None:
        """保存原始聊天记录"""
        path = self._get_contact_dir(contact_id) / 'raw_data.json'
        self._save_json(path, chat_data)

    def save_analysis_data(self, contact_id: int, analysis_type: str,
                           data_type: str, data: Dict) -> None:
        """保存分析数据"""
        path = self._get_contact_dir(contact_id) / analysis_type / f'{data_type}.json'
        self._save_json(path, data)

    def load_analysis_data(self, contact_id: int, analysis_type: str,
                           data_type: str) -> Optional[Dict]:
        """加载分析数据"""
        path = self._get_contact_dir(contact_id) / analysis_type / f'{data_type}.json'
        return self._load_json(path)

    def load_raw_data(self, contact_id: int) -> Optional[Dict]:
        """加载原始聊天记录数据"""
        path = self._get_contact_dir(contact_id) / 'raw_data.json'
        return self._load_json(path)

    def get_contact_data(self, contact_id: int) -> Dict:
        """获取联系人的所有分析数据"""
        result = {
            'basic': {},
            'interactive': {},
            'semantic': {}
        }

        for analysis_type in result.keys():
            dir_path = self._get_contact_dir(contact_id) / analysis_type
            if dir_path.exists():
                for file_name in dir_path.iterdir():
                    if file_name.is_file() and file_name.suffix == '.json':
                        data_type = file_name.stem  # 使用文件名作为数据类型
                        result[analysis_type][data_type] = self.load_analysis_data(
                            contact_id, analysis_type, data_type)

        return result
