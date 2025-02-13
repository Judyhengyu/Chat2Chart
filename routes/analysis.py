from flask import Blueprint, render_template, abort
from pathlib import Path
from typing import Dict, Optional, Tuple
import json
from dataclasses import dataclass


@dataclass
class UserInfo:
    """用户信息数据结构"""
    name: str
    nickname: str
    headImgUrl: str
    ExtraBuf: Dict

    @classmethod
    def from_dict(cls, data: Dict) -> 'UserInfo':
        """从字典创建用户信息实例"""
        return cls(
            name=data.get('name', ''),
            nickname=data.get('nickname', ''),
            headImgUrl=data.get('headImgUrl', ''),
            ExtraBuf=data.get('ExtraBuf', {})
        )

    def process_urls(self) -> None:
        """处理用户相关的URL，将http转换为https"""
        if self.headImgUrl.startswith('http://'):
            self.headImgUrl = self.headImgUrl.replace('http://', 'https://')

        moments_bg = self.ExtraBuf.get('朋友圈背景', '')
        if moments_bg and moments_bg.startswith('http://shmmsns.qpic.cn'):
            moments_bg = moments_bg.replace('http://', 'https://')
            self.ExtraBuf['朋友圈背景'] = moments_bg


class AnalysisService:
    """分析服务类"""

    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.contacts_file = Path('data/contacts.json')

    def load_contacts(self) -> list:
        """加载联系人列表"""
        if self.contacts_file.exists():
            return json.loads(self.contacts_file.read_text(encoding='utf-8'))
        return []

    def get_contact(self, contact_id: int) -> Optional[Dict]:
        """获取指定联系人信息"""
        contacts = self.load_contacts()
        return next((c for c in contacts if c['id'] == contact_id), None)

    @staticmethod
    def load_user_info(contact_path: Path) -> Optional[UserInfo]:
        """加载用户信息"""
        try:
            users_file = contact_path / 'users.json'
            if not users_file.exists():
                return None

            users_data = json.loads(users_file.read_text(encoding='utf-8'))
            user_info = UserInfo.from_dict(next(iter(users_data.values())))
            user_info.process_urls()
            return user_info
        except Exception as e:
            print(f"Error loading user info: {str(e)}")
            return None

    @staticmethod
    def calculate_stats(messages: list, stats: Dict) -> Dict:
        """计算统计指标"""
        total_messages = sum(stats['type_counts'].values()) if stats else 0

        # 计算消息比例
        sender_messages = sum(1 for msg in messages if msg.get('is_sender', False))
        receiver_messages = total_messages - sender_messages

        return {
            'total_messages': total_messages,
            'message_ratio': {
                'sender': {
                    'count': sender_messages,
                    'percentage': round(sender_messages / total_messages * 100, 1) if total_messages > 0 else 0
                },
                'receiver': {
                    'count': receiver_messages,
                    'percentage': round(receiver_messages / total_messages * 100, 1) if total_messages > 0 else 0
                }
            }
        }

    @staticmethod
    def get_activity_stats(time_stats: Dict) -> Tuple[int, str, int]:
        """获取活跃度统计"""
        weekday_map = {
            'Monday': '星期一', 'Tuesday': '星期二', 'Wednesday': '星期三',
            'Thursday': '星期四', 'Friday': '星期五', 'Saturday': '星期六',
            'Sunday': '星期日'
        }

        most_active_hour = max(time_stats['hourly_counts'].items(),
                               key=lambda x: x[1])[0] if time_stats else 0
        most_active_day = max(time_stats['weekday_counts'].items(),
                              key=lambda x: x[1])[0] if time_stats else '未知'
        most_active_day = weekday_map.get(most_active_day, most_active_day)

        avg_daily_messages = round(len(time_stats['daily_counts'])) if time_stats else 0

        return most_active_hour, most_active_day, avg_daily_messages


def create_blueprint(data_manager):
    bp = Blueprint('analysis', __name__)
    service = AnalysisService(data_manager)

    @bp.route('/contact/<int:contact_id>/<analysis_type>')
    def show_analysis(contact_id: int, analysis_type: str):
        """显示分析页面"""
        # 获取联系人信息
        contact = service.get_contact(contact_id)
        if not contact:
            abort(404, description='联系人不存在')

        # 加载数据
        try:
            user_info = service.load_user_info(Path(contact['path']))
            raw_data = data_manager.load_raw_data(contact_id)
            messages = raw_data.get('messages', []) if raw_data else []

            # 加载分析数据
            stats = data_manager.load_analysis_data(contact_id, 'basic', 'message_stats')
            time_stats = data_manager.load_analysis_data(contact_id, 'basic', 'time_stats')
            daily_stats = data_manager.load_analysis_data(contact_id, 'basic', 'daily_stats')

            # 计算统计指标
            basic_stats = service.calculate_stats(messages, stats)
            most_active_hour, most_active_day, avg_daily_messages = service.get_activity_stats(time_stats)

            # 准备模板数据
            template_data = {
                'contact': contact,
                'contacts': service.load_contacts(),
                'user_info': user_info,
                'total_messages': basic_stats['total_messages'],
                'message_ratio': basic_stats['message_ratio'],
                'most_active_hour': most_active_hour,
                'most_active_day': most_active_day,
                'avg_daily_messages': avg_daily_messages
            }

            # 根据分析类型返回对应模板
            templates = {
                'basic': 'analysis/basic.html',
                'interactive': 'analysis/interactive.html',
                'semantic': 'analysis/semantic.html'
            }

            if analysis_type not in templates:
                abort(404, description='分析类型不存在')

            return render_template(templates[analysis_type], **template_data)

        except Exception as e:
            print(f"Error processing analysis: {str(e)}")
            abort(500, description='处理分析数据时出错')

    return bp
