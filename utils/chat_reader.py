from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import json
from dataclasses import dataclass
import re


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

    def find_chat_files(self) -> List[Path]:
        """查找所有聊天记录CSV文件并按顺序排序"""
        csv_files = list(self.chat_dir.glob('*.csv'))
        if not csv_files:
            raise FileNotFoundError(f"未找到聊天记录文件: {self.chat_dir}/*.csv")
        
        # 使用正则表达式提取文件名中的数字范围
        def get_start_index(file_path: Path) -> int:
            match = re.search(r'_(\d+)_\d+\.csv$', file_path.name)
            return int(match.group(1)) if match else 0
        
        # 按照起始索引排序
        return sorted(csv_files, key=get_start_index)

    def read_chat_data(self) -> ChatData:
        """读取并处理聊天记录数据"""
        # 读取用户信息
        users = self.read_users()

        # 读取所有CSV文件并合并
        chat_files = self.find_chat_files()
        dfs = []
        
        for file in chat_files:
            try:
                df = pd.read_csv(file)
                dfs.append(df)
            except Exception as e:
                print(f"警告：读取文件 {file} 时出错: {str(e)}")
                continue

        if not dfs:
            raise Exception("没有成功读取任何聊天记录文件")

        # 合并所有数据框
        df = pd.concat(dfs, ignore_index=True)
        
        # 去重（以防万一）
        df = df.drop_duplicates()
        
        # 按时间排序
        df['CreateTime'] = pd.to_datetime(df['CreateTime'])
        df = df.sort_values('CreateTime')

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
