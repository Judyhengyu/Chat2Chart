from pathlib import Path
from typing import Dict, Any
import pandas as pd
import json
from dataclasses import dataclass, asdict


@dataclass
class ChatData:
    """聊天数据结构"""
    users: Dict
    messages: Any  # 可以是 DataFrame 或 list
    stats: Dict

    def to_dict(self) -> Dict:
        """转换为可序列化的字典"""
        return {
            'users': self.users,
            'messages': self.messages.to_dict('records') if isinstance(self.messages, pd.DataFrame) else self.messages,
            'stats': self.stats
        }


class ChatReader:
    def __init__(self, chat_dir: str):
        """初始化聊天记录读取器
        Args:
            chat_dir: 聊天记录目录路径
        """
        self.chat_dir = Path(chat_dir)
        self.users_file = self.chat_dir / 'users.json'

    def read_users(self) -> Dict:
        """读取用户信息"""
        if not self.users_file.exists():
            raise FileNotFoundError(f"用户信息文件不存在: {self.users_file}")
        return json.loads(self.users_file.read_text(encoding='utf-8'))

    def find_chat_file(self) -> Path:
        """查找聊天记录CSV文件"""
        csv_files = list(self.chat_dir.glob('*.csv'))
        if not csv_files:
            raise FileNotFoundError(f"未找到聊天记录文件: {self.chat_dir}/*.csv")
        return csv_files[0]

    def read_chat_data(self) -> ChatData:
        """读取并处理聊天记录数据"""
        # 读取用户信息
        users = self.read_users()

        # 读取聊天记录
        chat_file = self.find_chat_file()
        df = pd.read_csv(chat_file)

        # 处理时间格式
        df['CreateTime'] = pd.to_datetime(df['CreateTime'])

        return ChatData(
            users=users,
            messages=df,
            stats=self._calculate_stats(df)
        )

    @staticmethod
    def _calculate_stats(df: pd.DataFrame) -> Dict:
        """计算基础统计信息"""
        return {
            'total_messages': len(df),
            'start_time': df['CreateTime'].min().strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': df['CreateTime'].max().strftime('%Y-%m-%d %H:%M:%S'),
            'message_types': df['type_name'].value_counts().to_dict()
        }


def read_chat_data(chat_dir: str) -> Dict:
    """读取聊天记录的主函数
    Args:
        chat_dir: 聊天记录目录路径
    Returns:
        dict: 包含用户信息和聊天记录的数据结构
    """
    try:
        reader = ChatReader(chat_dir)
        chat_data = reader.read_chat_data()
        return chat_data.to_dict()  # 返回可序列化的字典
    except Exception as e:
        raise Exception(f"读取聊天记录失败: {str(e)}")
