def create_routes(app, data_manager):
    from .basic import create_blueprint as create_basic_bp
    from .contacts import create_blueprint as create_contacts_bp
    from .analysis import create_blueprint as create_analysis_bp
    
    # 注册蓝图
    app.register_blueprint(create_basic_bp(data_manager))
    app.register_blueprint(create_contacts_bp(data_manager))
    app.register_blueprint(create_analysis_bp(data_manager)) 