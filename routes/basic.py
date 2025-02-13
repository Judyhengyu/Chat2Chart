from flask import Blueprint, jsonify
from utils.analyzers.message_length import analyze_message_length


def create_blueprint(data_manager):
    bp = Blueprint('basic', __name__)

    @bp.route('/api/contacts/<int:contact_id>/basic/stats')
    def get_basic_stats(contact_id):
        try:
            raw_data = data_manager.load_raw_data(contact_id)
            if not raw_data:
                return jsonify({'error': '数据不存在'}), 404

            messages = raw_data.get('messages', [])
            message_length_stats = analyze_message_length(messages)

            return jsonify({
                'message_stats': data_manager.load_analysis_data(contact_id, 'basic', 'message_stats'),
                'time_stats': data_manager.load_analysis_data(contact_id, 'basic', 'time_stats'),
                'daily_stats': data_manager.load_analysis_data(contact_id, 'basic', 'daily_stats'),
                'message_length': message_length_stats
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return bp
