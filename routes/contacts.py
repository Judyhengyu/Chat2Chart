import shutil
from pathlib import Path
from typing import Dict, List, Optional
import json
from flask import Blueprint, jsonify, request, render_template, current_app
from dataclasses import dataclass
from datetime import datetime

from utils.chat_reader import read_chat_data
from utils.analyzer import (
    analyze_basic_stats,
    analyze_interactive_patterns,
    analyze_semantic_content,
    ChatAnalyzer
)
import pandas as pd


@dataclass
class ContactInfo:
    """联系人信息数据结构"""
    id: int
    name: str
    path: str

    @classmethod
    def from_dict(cls, data: Dict) -> 'ContactInfo':
        return cls(
            id=data['id'],
            name=data['name'],
            path=data['path']
        )

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'path': self.path
        }


class ContactService:
    """联系人服务类"""

    def __init__(self, data_manager):
        self.data_manager = data_manager

    def load_contacts(self) -> List[ContactInfo]:
        """加载联系人列表"""
        contacts_file = self.data_manager.paths.CONTACTS_FILE
        if contacts_file.exists():
            data = json.loads(contacts_file.read_text(encoding='utf-8'))
            return [ContactInfo.from_dict(c) for c in data]
        return []

    def save_contacts(self, contacts: List[ContactInfo]) -> None:
        """保存联系人列表"""
        data = [c.to_dict() for c in contacts]
        self.data_manager.paths.CONTACTS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2)
        )

    def analyze_and_save_data(self, contact_id: int, chat_data: Dict) -> None:
        """分析并保存数据"""
        # 基础分析
        basic_stats = analyze_basic_stats(chat_data)
        for data_type, data in basic_stats.items():
            self.data_manager.save_analysis_data(contact_id, 'basic', data_type, data)

        # 交互分析
        interactive_stats = analyze_interactive_patterns(chat_data)
        for data_type, data in interactive_stats.items():
            self.data_manager.save_analysis_data(contact_id, 'interactive', data_type, data)

    def create_contact(self, name: str, path: str) -> Optional[ContactInfo]:
        """创建新联系人"""
        if not name or not path:
            raise ValueError('缺少必要参数')

        if not Path(path).exists():
            raise ValueError('聊天记录路径不存在')

        contacts = self.load_contacts()
        contact_id = len(contacts) + 1

        new_contact = ContactInfo(id=contact_id, name=name, path=path)

        # 初始化数据目录
        self.data_manager.init_contact_directory(contact_id)

        # 读取并保存聊天记录
        chat_data = read_chat_data(path)
        self.data_manager.save_raw_data(contact_id, chat_data)

        # 分析数据
        self.analyze_and_save_data(contact_id, chat_data)

        contacts.append(new_contact)
        self.save_contacts(contacts)

        return new_contact

    def delete_contact(self, contact_id: int) -> None:
        """删除联系人"""
        contacts = self.load_contacts()
        contacts = [c for c in contacts if c.id != contact_id]
        self.save_contacts(contacts)

        # 删除数据目录
        contact_dir = self.data_manager._get_contact_dir(contact_id)
        if contact_dir.exists():
            shutil.rmtree(contact_dir)

    def update_contact(self, contact_id: int, name: str) -> Optional[ContactInfo]:
        """更新联系人信息"""
        contacts = self.load_contacts()
        contact = next((c for c in contacts if c.id == contact_id), None)

        if not contact:
            return None

        contact.name = name
        self.save_contacts(contacts)
        return contact


def create_blueprint(data_manager):
    bp = Blueprint('contacts', __name__)
    service = ContactService(data_manager)

    @bp.route('/contact/<int:contact_id>/<analysis_type>')
    def show_analysis(contact_id, analysis_type):
        """显示分析页面"""
        contacts = service.load_contacts()
        contact = next((c for c in contacts if c.id == contact_id), None)

        if not contact:
            return '联系人不存在', 404

        try:
            # 读取用户信息
            with open(Path(contact.path) / 'users.json', 'r', encoding='utf-8') as f:
                users_data = json.load(f)
                user_info = next(iter(users_data.values()))

                # 处理朋友圈背景图片URL
                moments_bg = user_info.get('ExtraBuf', {}).get('朋友圈背景', '')
                if moments_bg and moments_bg.startswith('http://shmmsns.qpic.cn'):
                    moments_bg = moments_bg.replace('http://', 'https://')
                    user_info['ExtraBuf']['朋友圈背景'] = moments_bg

                # 处理头像URL
                if user_info.get('headImgUrl', '').startswith('http://'):
                    user_info['headImgUrl'] = user_info['headImgUrl'].replace('http://', 'https://')

            # 读取原始消息数据
            raw_data = data_manager.load_raw_data(contact_id)
            messages = raw_data.get('messages', []) if raw_data else []

        except Exception as e:
            print(f"Error loading data: {str(e)}")
            user_info = {}
            messages = []

        # 加载分析数据
        stats = data_manager.load_analysis_data(contact_id, 'basic', 'message_stats')
        time_stats = data_manager.load_analysis_data(contact_id, 'basic', 'time_stats')
        daily_stats = data_manager.load_analysis_data(contact_id, 'basic', 'daily_stats')

        # 计算统计指标
        total_messages = sum(stats['type_counts'].values()) if stats else 0
        most_active_hour = max(time_stats['hourly_counts'].items(), key=lambda x: x[1])[0] if time_stats else 0
        most_active_day = max(time_stats['weekday_counts'].items(), key=lambda x: x[1])[0] if time_stats else '未知'

        # 计算平均消息数
        avg_daily_messages = round(
            total_messages / len(daily_stats['daily_counts'])) if daily_stats and daily_stats.get('daily_counts') else 0

        # 转换星期几为中文
        weekday_map = {
            'Monday': '星期一',
            'Tuesday': '星期二',
            'Wednesday': '星期三',
            'Thursday': '星期四',
            'Friday': '星期五',
            'Saturday': '星期六',
            'Sunday': '星期日'
        }
        most_active_day = weekday_map.get(most_active_day, most_active_day)

        # 计算双方消息占比
        sender_messages = sum(1 for msg in messages if msg.get('is_sender', False))
        receiver_messages = total_messages - sender_messages
        message_ratio = {
            'sender': {
                'count': sender_messages,
                'percentage': round(sender_messages / total_messages * 100, 1) if total_messages > 0 else 0
            },
            'receiver': {
                'count': receiver_messages,
                'percentage': round(receiver_messages / total_messages * 100, 1) if total_messages > 0 else 0
            }
        }

        template_data = {
            'contact': contact.to_dict(),
            'contacts': [c.to_dict() for c in contacts],
            'total_messages': total_messages,
            'message_ratio': message_ratio,
            'most_active_hour': most_active_hour,
            'most_active_day': most_active_day,
            'avg_daily_messages': avg_daily_messages,
            'user_info': user_info
        }

        if analysis_type == 'basic':
            return render_template('analysis/basic.html', **template_data)
        elif analysis_type == 'interactive':
            return render_template('analysis/interactive.html', **template_data)
        elif analysis_type == 'semantic':
            return render_template('analysis/semantic.html', **template_data)
        else:
            return '分析类型不存在', 404

    @bp.route('/api/contacts/<int:contact_id>/basic/stats')
    def get_basic_stats(contact_id):
        """获取基础统计数据"""
        try:
            stats = data_manager.load_analysis_data(contact_id, 'basic', 'message_stats')
            time_stats = data_manager.load_analysis_data(contact_id, 'basic', 'time_stats')
            daily_stats = data_manager.load_analysis_data(contact_id, 'basic', 'daily_stats')

            return jsonify({
                'message_stats': stats,
                'time_stats': time_stats,
                'daily_stats': daily_stats
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/contacts/<int:contact_id>/interactive/stats')
    def get_interactive_stats(contact_id):
        """获取交互统计数据"""
        try:
            chat_pattern = data_manager.load_analysis_data(contact_id, 'interactive', 'chat_pattern')
            response_time = data_manager.load_analysis_data(contact_id, 'interactive', 'response_time')
            heatmap = data_manager.load_analysis_data(contact_id, 'interactive', 'heatmap')
            interaction = data_manager.load_analysis_data(contact_id, 'interactive', 'interaction')

            return jsonify({
                'chat_pattern': chat_pattern,
                'response_time': response_time,
                'heatmap': heatmap,
                'interaction': interaction
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/contacts/<int:contact_id>/semantic/stats')
    def get_semantic_stats(contact_id):
        """获取语义统计数据"""
        try:
            keywords = data_manager.load_analysis_data(contact_id, 'semantic', 'keywords')
            topics = data_manager.load_analysis_data(contact_id, 'semantic', 'topics')
            sentiment = data_manager.load_analysis_data(contact_id, 'semantic', 'sentiment')
            tags = data_manager.load_analysis_data(contact_id, 'semantic', 'tags')

            return jsonify({
                'keywords': keywords,
                'topics': topics,
                'sentiment': sentiment,
                'tags': tags
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/contacts/new', methods=['POST'])
    def new_contact():
        """创建新联系人"""
        try:
            contact = service.create_contact(
                name=request.form.get('name'),
                path=request.form.get('path')
            )
            return jsonify(contact.to_dict())
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/contacts/<int:contact_id>/delete', methods=['DELETE'])
    def delete_contact(contact_id):
        """删除联系人"""
        try:
            service.delete_contact(contact_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/contacts/<int:contact_id>/edit', methods=['PUT'])
    def edit_contact(contact_id):
        """编辑联系人"""
        try:
            data = request.get_json()
            contact = service.update_contact(contact_id, data.get('name'))

            if not contact:
                return jsonify({'error': '联系人不存在'}), 404

            return jsonify({
                'success': True,
                'contact': contact.to_dict()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/contacts/<int:contact_id>/semantic/generate/<analysis_type>')
    def generate_semantic_analysis(contact_id, analysis_type):
        """生成语义分析数据"""
        try:
            # 加载原始聊天数据
            chat_data = data_manager.load_raw_data(contact_id)
            if not chat_data:
                return jsonify({'error': '找不到聊天记录数据'}), 404

            # 创建分析器实例
            analyzer = ChatAnalyzer(chat_data)

            # 根据分析类型生成对应的数据
            if analysis_type == 'keywords':
                result = analyzer.analyze_semantic_content()['keywords']
                data_manager.save_analysis_data(contact_id, 'semantic', 'keywords', result)
                return jsonify(result)

            elif analysis_type == 'topics':
                result = analyzer.analyze_semantic_content()['topics']
                data_manager.save_analysis_data(contact_id, 'semantic', 'topics', result)
                return jsonify(result)

            elif analysis_type == 'sentiment':
                result = analyzer.analyze_semantic_content()['sentiment']
                data_manager.save_analysis_data(contact_id, 'semantic', 'sentiment', result)
                return jsonify(result)

            elif analysis_type == 'tags':
                granularity = request.args.get('granularity', 'month')
                result = analyzer._analyze_tag_trends(
                    pd.DataFrame(chat_data['messages']),
                    granularity=granularity
                )
                data_manager.save_analysis_data(contact_id, 'semantic', 'tags', result)
                return jsonify(result)

            else:
                return jsonify({'error': '不支持的分析类型'}), 400

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/index')
    def index():
        """数据总览页面"""
        contacts = service.load_contacts()
        recent_contacts = []
        total_messages = 0
        earliest_time = None
        latest_time = None

        for contact in contacts[-6:]:  # 最近6个联系人
            try:
                contact_data = _get_contact_overview(contact, data_manager)
                if contact_data:
                    recent_contacts.append(contact_data)
                    total_messages += contact_data['total_messages']

                    if earliest_time is None or contact_data['earliest_time'] < earliest_time:
                        earliest_time = contact_data['earliest_time']
                    if latest_time is None or contact_data['latest_time'] > latest_time:
                        latest_time = contact_data['latest_time']

            except Exception as e:
                print(f"Error processing contact {contact.name}: {str(e)}")
                continue

        date_range = _format_date_range(earliest_time, latest_time)

        return render_template('index.html',
                               contacts=[c.to_dict() for c in contacts],
                               recent_contacts=recent_contacts,
                               total_messages=total_messages,
                               date_range=date_range)

    @bp.route('/api/dashboard/stats')
    def get_dashboard_stats():
        """获取数据总览统计数据"""
        try:
            contacts = service.load_contacts()
            message_types = {}
            active_times = {str(i): 0 for i in range(24)}

            for contact in contacts:
                # 获取消息类型统计
                stats = data_manager.load_analysis_data(contact.id, 'basic', 'message_stats')
                if stats and 'type_counts' in stats:
                    for msg_type, count in stats['type_counts'].items():
                        message_types[msg_type] = message_types.get(msg_type, 0) + count

                # 获取活跃时段统计
                time_stats = data_manager.load_analysis_data(contact.id, 'basic', 'time_stats')
                if time_stats and 'hourly_counts' in time_stats:
                    for hour, count in time_stats['hourly_counts'].items():
                        active_times[str(hour)] = active_times.get(str(hour), 0) + count

            return jsonify({
                'message_types': message_types,
                'active_times': active_times
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/contacts/<int:contact_id>/update', methods=['POST'])
    def update_contact_data(contact_id):
        """更新联系人数据"""
        try:
            # 获取联系人信息
            contacts = service.load_contacts()
            contact = next((c for c in contacts if c.id == contact_id), None)
            if not contact:
                return jsonify({'error': '联系人不存在'}), 404

            # 重新读取并分析数据
            chat_data = read_chat_data(contact.path)
            service.analyze_and_save_data(contact_id, chat_data)

            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return bp


def _get_contact_overview(contact: ContactInfo, data_manager) -> Optional[Dict]:
    """获取联系人概览数据"""
    users_file = Path(contact.path) / 'users.json'
    if not users_file.exists():
        return None

    users_data = json.loads(users_file.read_text(encoding='utf-8'))
    user_info = next(iter(users_data.values()))

    # 处理头像URL
    avatar_url = user_info.get('headImgUrl', '')
    if avatar_url.startswith('http://'):
        avatar_url = avatar_url.replace('http://', 'https://')

    raw_data = data_manager.load_raw_data(contact.id)
    if not raw_data or not raw_data.get('messages'):
        return None

    messages = raw_data['messages']
    msg_times = [datetime.fromisoformat(msg['CreateTime']) for msg in messages]

    return {
        'id': contact.id,
        'name': contact.name,
        'avatar_url': avatar_url,
        'total_messages': len(messages),
        'earliest_time': min(msg_times),
        'latest_time': max(msg_times),
        'last_analyzed': max(msg_times).strftime('%Y-%m-%d %H:%M')
    }


def _format_date_range(earliest_time: Optional[datetime],
                       latest_time: Optional[datetime]) -> str:
    """格式化日期范围"""
    if not earliest_time or not latest_time:
        return '暂无数据'

    if earliest_time.year == latest_time.year:
        if earliest_time.month == latest_time.month:
            return earliest_time.strftime('%Y年%m月')
        return f"{earliest_time.strftime('%Y年%m月')} - {latest_time.strftime('%m月')}"
    return f"{earliest_time.strftime('%Y年%m月')} - {latest_time.strftime('%Y年%m月')}"
