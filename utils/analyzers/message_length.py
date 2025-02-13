def analyze_message_length(messages):
    """分析消息长度"""
    # 文字消息分析
    sender_text_messages = [msg for msg in messages
                            if msg.get('type_name') == '文本' and msg.get('is_sender')]
    receiver_text_messages = [msg for msg in messages
                              if msg.get('type_name') == '文本' and not msg.get('is_sender')]

    # 计算文字消息平均长度
    sender_text_lengths = [len(msg.get('msg', '')) for msg in sender_text_messages if msg.get('msg')]
    receiver_text_lengths = [len(msg.get('msg', '')) for msg in receiver_text_messages if msg.get('msg')]

    # 语音消息分析
    def extract_voice_length(msg):
        content = msg.get('msg', '')
        if isinstance(content, str) and '语音时长：' in content:
            try:
                length_str = content.split('语音时长：')[1].split('秒')[0].strip()
                return float(length_str)
            except (ValueError, IndexError):
                return 0
        return 0

    sender_voice_messages = [msg for msg in messages
                             if msg.get('type_name') == '语音' and msg.get('is_sender')]
    receiver_voice_messages = [msg for msg in messages
                               if msg.get('type_name') == '语音' and not msg.get('is_sender')]

    # 计算语音消息平均长度
    sender_voice_lengths = [l for l in [extract_voice_length(msg) for msg in sender_voice_messages] if l > 0]
    receiver_voice_lengths = [l for l in [extract_voice_length(msg) for msg in receiver_voice_messages] if l > 0]

    # 语音通话分析
    def extract_call_duration(msg):
        content = msg.get('msg', '')
        if isinstance(content, str) and '通话时长' in content:
            try:
                duration_str = content.split('通话时长')[1].strip().strip('[]').strip()
                minutes, seconds = map(int, duration_str.split(':'))
                return minutes * 60 + seconds
            except (ValueError, IndexError):
                return 0
        return 0

    call_messages = [msg for msg in messages if msg.get('type_name') == '语音通话']
    call_durations = [d for d in [extract_call_duration(msg) for msg in call_messages] if d > 0]

    return {
        'text_length': {
            'sender_average': round(sum(sender_text_lengths) / len(sender_text_lengths)) if sender_text_lengths else 0,
            'receiver_average': round(
                sum(receiver_text_lengths) / len(receiver_text_lengths)) if receiver_text_lengths else 0,
            'sender_count': len(sender_text_messages),
            'receiver_count': len(receiver_text_messages)
        },
        'voice_length': {
            'sender_average': round(sum(sender_voice_lengths) / len(sender_voice_lengths),
                                    1) if sender_voice_lengths else 0,
            'receiver_average': round(sum(receiver_voice_lengths) / len(receiver_voice_lengths),
                                      1) if receiver_voice_lengths else 0,
            'sender_count': len(sender_voice_messages),
            'receiver_count': len(receiver_voice_messages)
        },
        'call_duration': {
            'average': round(sum(call_durations) / len(call_durations), 1) if call_durations else 0,
            'count': len(call_messages)
        }
    }
