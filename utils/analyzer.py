from dataclasses import dataclass
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import jieba
import jieba.analyse
from snownlp import SnowNLP
import json
from pathlib import Path


@dataclass
class AnalysisConfig:
    """分析配置"""
    RESPONSE_TIME_THRESHOLD: int = 3600  # 响应时间阈值(秒)
    KEYWORDS_TOP_K: int = 20  # 关键词提取数量
    SENTIMENT_THRESHOLDS: Tuple[float, float] = (0.4, 0.6)  # 情感分析阈值


class ChatAnalyzer:
    def __init__(self, chat_data: Dict):
        """初始化分析器
        Args:
            chat_data: 包含用户信息和消息数据的字典
        """
        self.users = chat_data['users']
        self.messages_df = pd.DataFrame(chat_data['messages'])
        self.stats = chat_data['stats']
        self._preprocess_data()

    def _preprocess_data(self) -> None:
        """预处理数据"""
        # 确保时间列为datetime类型
        self.messages_df['CreateTime'] = pd.to_datetime(self.messages_df['CreateTime'])
        # 添加小时列用于时间分析
        self.messages_df['hour'] = self.messages_df['CreateTime'].dt.hour
        # 添加日期列用于日期分析
        self.messages_df['date'] = self.messages_df['CreateTime'].dt.date

    @property
    def text_messages(self) -> pd.DataFrame:
        """获取文本消息"""
        return self.messages_df[self.messages_df['type_name'] == '文本']

    def analyze_basic_stats(self) -> Dict:
        """基础统计分析"""
        message_stats = self._analyze_message_types()
        time_stats = self._analyze_time_distribution()
        daily_stats = self._analyze_daily_stats()

        return {
            'message_stats': message_stats,
            'time_stats': time_stats,
            'daily_stats': daily_stats
        }

    def _analyze_message_types(self) -> Dict:
        """分析消息类型分布"""
        type_counts = self.messages_df['type_name'].value_counts()
        return {
            'type_counts': type_counts.to_dict(),
            'type_percentages': (type_counts.div(len(self.messages_df)) * 100).round(2).to_dict()
        }

    def _analyze_time_distribution(self) -> Dict:
        """分析时间分布"""
        return {
            'hourly_counts': self.messages_df['hour'].value_counts().sort_index().to_dict(),
            'weekday_counts': self.messages_df['CreateTime'].dt.day_name().value_counts().to_dict(),
            'monthly_counts': self.messages_df['CreateTime'].dt.to_period('M').astype(
                str).value_counts().sort_index().to_dict()
        }

    def _analyze_daily_stats(self) -> Dict:
        """分析每日统计"""
        # 将日期转换为字符串格式
        self.messages_df['date_str'] = self.messages_df['date'].astype(str)

        # 使用字符串格式的日期进行分组
        daily_counts = self.messages_df.groupby('date_str').size()
        daily_types = self.messages_df.groupby(['date_str', 'type_name']).size().unstack(fill_value=0)

        return {
            'daily_counts': daily_counts.to_dict(),
            'daily_types': daily_types.to_dict()
        }

    def analyze_interactive_patterns(self) -> Dict:
        """交互模式分析"""
        return {
            'chat_pattern': {'conversation_gaps': self._analyze_conversation_gaps()},
            'response_time': {'response_distribution': self._analyze_response_distribution()},
            'heatmap': self._analyze_chat_heatmap(),
            'interaction': self._analyze_chat_interaction()
        }

    def _get_response_times(self) -> List[float]:
        """获取响应时间列表"""
        df = self.messages_df
        mask = (df['is_sender'] != df['is_sender'].shift()) & \
               (df['CreateTime'].diff().dt.total_seconds() < AnalysisConfig.RESPONSE_TIME_THRESHOLD)
        return df[mask]['CreateTime'].diff().dt.total_seconds().dropna().tolist()

    def _calculate_avg_response_time(self):
        """计算平均响应时间"""
        response_times = self._get_response_times()
        return np.mean(response_times) if response_times else 0

    def _analyze_response_distribution(self) -> Dict:
        """分析响应时间分布"""
        response_times = pd.Series(self._get_response_times())
        bins = [0, 60, 300, 900, 1800, 3600]
        labels = ['1分钟内', '5分钟内', '15分钟内', '30分钟内', '1小时内']

        if not response_times.empty:
            distribution = pd.cut(response_times, bins=bins, labels=labels, right=False).value_counts()
            return distribution.to_dict()
        return {label: 0 for label in labels}

    def _analyze_interaction_frequency(self):
        """分析互动频率"""
        df = self.messages_df
        return {
            'by_hour': df.groupby(df['CreateTime'].dt.hour).size().to_dict(),
            'by_weekday': df.groupby(df['CreateTime'].dt.dayofweek).size().to_dict(),
            'by_month': df.groupby(df['CreateTime'].dt.month).size().to_dict()
        }

    def _analyze_chat_interaction(self):
        """分析聊天互动情况"""
        df = self.messages_df

        # 按日期分组消息
        df['date'] = df['CreateTime'].dt.date
        daily_messages = df.groupby('date').agg(list).reset_index()

        # 统计发起和结束对话的次数
        initiator_stats = {'sender': 0, 'receiver': 0}
        ender_stats = {'sender': 0, 'receiver': 0}

        for _, day in daily_messages.iterrows():
            messages = day['is_sender']
            if len(messages) > 0:
                # 判断对话发起者
                first_msg = messages[0]
                initiator_stats['sender' if first_msg == 1 else 'receiver'] += 1

                # 判断对话结束者
                last_msg = messages[-1]
                ender_stats['sender' if last_msg == 1 else 'receiver'] += 1

        total_days = len(daily_messages)

        return {
            'initiator': {
                'sender_percent': round(initiator_stats['sender'] / total_days * 100, 1),
                'receiver_percent': round(initiator_stats['receiver'] / total_days * 100, 1),
                'sender_count': initiator_stats['sender'],
                'receiver_count': initiator_stats['receiver']
            },
            'ender': {
                'sender_percent': round(ender_stats['sender'] / total_days * 100, 1),
                'receiver_percent': round(ender_stats['receiver'] / total_days * 100, 1),
                'sender_count': ender_stats['sender'],
                'receiver_count': ender_stats['receiver']
            }
        }

    def _analyze_conversation_gaps(self):
        """分析对话间隔"""
        df = self.messages_df

        # 按时间排序
        df = df.sort_values('CreateTime')

        # 计算时间差（小时）
        time_diffs = []
        for i in range(1, len(df)):
            time_diff = (df.iloc[i]['CreateTime'] - df.iloc[i - 1]['CreateTime']).total_seconds() / 3600
            time_diffs.append(time_diff)

        if time_diffs:
            # 定义时间间隔的边界（小时）
            bins = [0, 1, 2, 3, 4, 5, 6, 12, 24, float('inf')]
            labels = ['1小时内', '1-2小时', '2-3小时', '3-4小时', '4-5小时',
                      '5-6小时', '6-12小时', '12-24小时', '24小时以上']

            # 使用 pandas 的 cut 函数进行分类
            gap_series = pd.Series(time_diffs)
            gap_categories = pd.cut(gap_series,
                                    bins=bins,
                                    labels=labels,
                                    include_lowest=True)

            distribution = gap_categories.value_counts().to_dict()

            # 确保所有类别都存在
            all_categories = {label: 0 for label in labels}
            all_categories.update(distribution)
            distribution = all_categories

            # 计算平均间隔和最大间隔（小时）
            avg_gap = np.mean(time_diffs)
            max_gap = max(time_diffs)
        else:
            distribution = {label: 0 for label in
                            ['1小时内', '1-2小时', '2-3小时', '3-4小时', '4-5小时', '5-6小时', '6-12小时', '12-24小时',
                             '24小时以上']}
            avg_gap = 0
            max_gap = 0

        return {
            'count': len(time_diffs),
            'avg_gap': round(avg_gap, 1),
            'max_gap': round(max_gap, 1),
            'distribution': distribution
        }

    def _analyze_chat_heatmap(self):
        """分析聊天热力图数据"""
        df = self.messages_df

        # 确保 CreateTime 是 datetime 类型
        df['CreateTime'] = pd.to_datetime(df['CreateTime'])

        # 按日期统计消息数量（使用日期字符串作为索引）
        daily_counts = df.groupby(df['CreateTime'].dt.strftime('%Y-%m-%d')).size()

        # 生成热力图数据
        heatmap_data = []
        max_count = 0

        # 生成完整的日期范围
        start_date = df['CreateTime'].min().date()
        end_date = df['CreateTime'].max().date()
        date_range = pd.date_range(start_date, end_date)

        # 对每一天生成数据，包括没有消息的日期
        for date in date_range:
            date_str = date.strftime('%Y-%m-%d')
            count = daily_counts.get(date_str, 0)  # 如果没有消息，返回0
            heatmap_data.append([date_str, int(count)])
            max_count = max(max_count, count)

        # 定义消息数量的区间（使用红色系）
        max_daily = max_count
        pieces = [
            {'min': 0, 'max': max_daily * 0.1, 'label': f'0-{int(max_daily * 0.1)}', 'color': '#FFEBEE'},  # 最浅红
            {'min': max_daily * 0.1, 'max': max_daily * 0.3, 'label': f'{int(max_daily * 0.1)}-{int(max_daily * 0.3)}',
             'color': '#FFCDD2'},  # 浅红
            {'min': max_daily * 0.3, 'max': max_daily * 0.5, 'label': f'{int(max_daily * 0.3)}-{int(max_daily * 0.5)}',
             'color': '#EF9A9A'},  # 中红
            {'min': max_daily * 0.5, 'max': max_daily * 0.7, 'label': f'{int(max_daily * 0.5)}-{int(max_daily * 0.7)}',
             'color': '#E57373'},  # 深红
            {'min': max_daily * 0.7, 'label': f'{int(max_daily * 0.7)}+', 'color': '#F44336'}  # 最深红
        ]

        return {
            'data': heatmap_data,
            'max_count': max_count,
            'date_range': [start_date.strftime('%Y-%m-%d'),
                           end_date.strftime('%Y-%m-%d')],
            'pieces': pieces
        }

    def analyze_semantic_content(self) -> Dict:
        """语义内容分析"""
        text = ' '.join(self.text_messages['msg'].fillna(''))
        return {
            'keywords': {
                'tfidf': self._extract_keywords(text, 'tfidf'),
                'textrank': self._extract_keywords(text, 'textrank')
            },
            'topics': self._analyze_topics(text),
            'sentiment': self._analyze_sentiment(self.text_messages)
        }

    @staticmethod
    def _extract_keywords(text: str, method: str = 'tfidf', topK: int = AnalysisConfig.KEYWORDS_TOP_K) -> List[
        Tuple[str, float]]:
        """提取关键词
        Args:
            text: 文本内容
            method: 提取方法 ('tfidf' 或 'textrank')
            topK: 返回前K个关键词
        """
        extractor = jieba.analyse.extract_tags if method == 'tfidf' else jieba.analyse.textrank
        return extractor(text, topK=topK, withWeight=True)

    @staticmethod
    def _analyze_topics(text):
        """话题分析"""
        # 使用 jieba 提取关键词
        keywords = jieba.analyse.extract_tags(text, topK=100, withWeight=True)

        # 处理关键词和权重
        processed_keywords = []
        frequencies = []
        for word, weight in keywords[:20]:  # 只取前20个关键词
            processed_keywords.append(word)
            frequencies.append(round(weight * 100, 1))  # 将权重转换为百分比

        return {
            'keywords': processed_keywords,
            'topic_frequencies': frequencies,
            'topic_count': len(processed_keywords)
        }

    @staticmethod
    def _analyze_sentiment(messages: pd.DataFrame) -> Dict[str, float]:
        """情感分析"""
        sentiments = []
        for text in messages['msg'].dropna():
            try:
                sentiments.append(SnowNLP(text).sentiments)
            except:
                continue

        if not sentiments:
            return {'positive': 0, 'neutral': 0, 'negative': 0}

        sentiments = pd.Series(sentiments)
        low, high = AnalysisConfig.SENTIMENT_THRESHOLDS
        counts = pd.cut(sentiments,
                        bins=[-np.inf, low, high, np.inf],
                        labels=['negative', 'neutral', 'positive']).value_counts()

        total = len(sentiments)
        return {k: round(v / total * 100, 1) for k, v in counts.items()}

    @staticmethod
    def _analyze_tag_trends(messages_df: pd.DataFrame, granularity: str = 'month') -> Dict:
        """分析标签趋势"""
        # 加载话题和情感关键词映射
        base_dir = Path(__file__).parent.parent
        with open(base_dir / 'utils/text_analysis_data/basic_topics.json', 'r', encoding='utf-8') as f:
            basic_topics = json.load(f)
        with open(base_dir / 'utils/text_analysis_data/emotion_topics.json', 'r', encoding='utf-8') as f:
            emotion_topics = json.load(f)

        # 设置重采样频率
        freq_map = {'month': 'M', 'week': 'W', 'day': 'D'}
        date_format_map = {'month': '%Y-%m', 'week': '%Y-%m-%d', 'day': '%Y-%m-%d'}

        # 确保 CreateTime 是 datetime 类型并设置为索引
        messages_df = messages_df.copy()
        messages_df['CreateTime'] = pd.to_datetime(messages_df['CreateTime'])
        messages_df.set_index('CreateTime', inplace=True)

        def check_keywords(text: str, key_words: List[str]) -> bool:
            """检查文本中是否包含任意关键词"""
            return any(keyword in text for keyword in key_words)

        results = {'times': [], 'basicTopics': {}, 'emotions': {}}

        # 初始化话题和情感的列表
        for topic in basic_topics:
            results['basicTopics'][topic] = []
        for emotion in emotion_topics:
            results['emotions'][emotion] = []

        # 按时间粒度重采样并分析
        resampled = messages_df.resample(freq_map[granularity])
        for name, group in resampled:
            results['times'].append(name.strftime(date_format_map[granularity]))  # type: ignore

            # 获取该时间段的文本消息
            text_messages = group[group['type_name'] == '文本']['msg'].astype(str).fillna('')
            text_list = text_messages.tolist()  # 转换为列表

            # 统计基础话题
            for topic, keywords in basic_topics.items():
                # 检查该时间段内的所有消息是否包含话题关键词
                has_topic = any(check_keywords(msg, keywords) for msg in text_list)
                results['basicTopics'][topic].append(1 if has_topic else 0)

            # 统计情感态度
            for emotion, keywords in emotion_topics.items():
                # 检查该时间段内的所有消息是否包含情感关键词
                has_emotion = any(check_keywords(msg, keywords) for msg in text_list)
                results['emotions'][emotion].append(1 if has_emotion else 0)

        return results


def analyze_basic_stats(chat_data):
    """基础统计分析入口函数"""
    analyzer = ChatAnalyzer(chat_data)
    return analyzer.analyze_basic_stats()


def analyze_interactive_patterns(chat_data):
    """交互模式分析入口函数"""
    analyzer = ChatAnalyzer(chat_data)
    return analyzer.analyze_interactive_patterns()


def analyze_semantic_content(chat_data):
    """语义内容分析入口函数"""
    analyzer = ChatAnalyzer(chat_data)
    return analyzer.analyze_semantic_content()
