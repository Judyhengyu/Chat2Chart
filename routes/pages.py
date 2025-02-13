from flask import Blueprint, render_template
import json
import os


def create_blueprint():
    bp = Blueprint('pages', __name__)

    @bp.route('/introduction')
    def introduction():
        """加载项目介绍页面"""
        # 加载联系人列表数据
        if os.path.exists('data/contacts.json'):
            with open('data/contacts.json', 'r', encoding='utf-8') as f:
                contacts = json.load(f)
        else:
            contacts = []

        return render_template('introduction.html', contacts=contacts)

    return bp
