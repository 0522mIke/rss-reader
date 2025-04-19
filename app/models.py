from datetime import datetime, timezone
from flask_login import UserMixin
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    is_demo = db.Column(db.Boolean, default=False)  # デモユーザ
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    feeds = db.relationship('Feed', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"User('{self.username}')"

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    feeds = db.relationship('Feed', backref='category', lazy=True)

    def __repr__(self):
        return f"Category('{self.name}')"

class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    articles = db.relationship('Article', backref='feed', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
    db.UniqueConstraint('user_id', 'url', name='unique_user_feed_url'),)

    def __repr__(self):
        return f"Feed('{self.title}')"

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(300), nullable=False)
    summary = db.Column(db.Text)
    published_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    feed_id = db.Column(db.Integer, db.ForeignKey('feed.id'), nullable=False)

    def __repr__(self):
        return f"Article('{self.title}')"