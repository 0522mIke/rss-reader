from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user
from werkzeug.security import generate_password_hash
from app.models import User
from app import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('feeds.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('feeds.dashboard'))
        else:
            flash('ログインに失敗しました。ユーザー名とパスワードを確認してください。', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('feeds.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # ユーザー名の重複チェック
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('このユーザー名は既に使用されています。', 'danger')
            return render_template('register.html')
            
        # ユーザー数の上限チェック
        user_count = User.query.count()
        if user_count >= 100:  # 最大100ユーザーまで
            flash('申し訳ありませんが、現在新規登録を受け付けていません。', 'danger')
            return render_template('register.html')
            
        # 新規ユーザー作成
        user = User(username=username)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('アカウントが作成されました。', 'success')
        return redirect(url_for('feeds.dashboard'))
    return render_template('register.html')

@auth_bp.route('/demo-login')
def demo_login():
    # デモユーザーを検索
    demo_user = User.query.filter_by(is_demo=True).first()
    
    # デモユーザーが存在しない場合は、通常の最初のユーザーを使用
    if not demo_user:
        demo_user = User.query.first()
        
    if demo_user:
        login_user(demo_user)
        return redirect(url_for('feeds.dashboard'))
    else:
        flash('デモユーザーが見つかりませんでした。', 'danger')
        return redirect(url_for('main.home'))

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('ログアウトしました', 'success')
    return redirect(url_for('auth.logout_complete'))


@auth_bp.route('/logout_complete')
def logout_complete():
    return render_template('logout.html')