import os
import certifi
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from datetime import timezone, timedelta
from dotenv import load_dotenv

# 環境変数とSSL設定
load_dotenv()
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['SSL_CERT_DIR'] = os.path.dirname(certifi.where())

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 拡張機能を初期化
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'このページにアクセスするにはログインしてください。'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    
    # 先頭の重複コードを削除
    # app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.feeds import feeds_bp
    from app.routes.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(feeds_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created")
            
        except Exception as e:
            logger.error(f"Database creation error: {str(e)}")
            raise

        # ここで初めてモデルをインポート（循環インポートを避けるため）
        from app.models import User, Category, Feed, Article
        from werkzeug.security import generate_password_hash

        demo_user = User.query.filter_by(is_demo=True).first()
        if not demo_user:
            demo_user = User(
                username='demo',
                password=generate_password_hash('demopass'),
                is_demo=True  # デモユーザーフラグをセット
            )
            db.session.add(demo_user)
            db.session.commit()

        default_categories = ['ニュース', 'テクノロジー', 'ビジネス', 'エンタメ', 'スポーツ', 'ライフスタイル', 'プログラミング', 'その他']
        for cat_name in default_categories:
            if not Category.query.filter_by(name=cat_name).first():
                db.session.add(Category(name=cat_name))
        db.session.commit()
        logger.info("Default categories created")

    return app