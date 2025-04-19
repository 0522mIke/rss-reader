from flask import Blueprint, render_template, redirect, url_for, request, flash
from app import db
from app.models import Feed, Article, Category
from app.utils.feed_handler import add_feed_for_user, update_feeds
from flask_login import login_required, current_user
from urllib.parse import unquote

feeds_bp = Blueprint('feeds', __name__, url_prefix='/feeds')

@feeds_bp.route('/dashboard')
@login_required
def dashboard():
    
    feeds = Feed.query.filter_by(user_id=current_user.id).all()
    selected_feed_id = request.args.get('feed_id', type=int)
    
    if not selected_feed_id and feeds:
        selected_feed_id = feeds[0].id
    
    if selected_feed_id:
        articles = Article.query.filter_by(feed_id=selected_feed_id)\
            .order_by(Article.published_date.desc()).limit(15).all()
        selected_feed = Feed.query.get_or_404(selected_feed_id)
    else:
        articles = []
        selected_feed = None
    
    categories = Category.query.all()
    return render_template('dashboard.html', 
                         feeds=feeds, 
                         articles=articles, 
                         selected_feed=selected_feed,
                         categories=categories)

@feeds_bp.route('/<category_name>')
@login_required
def filter_by_category(category_name):
    decoded_name = unquote(category_name)
    category = Category.query.filter_by(name=category_name).first_or_404()
    feeds = Feed.query.filter_by(category_id=category.id).all()
    return render_template('dashboard.html', 
                         feeds=feeds, 
                         articles=[],
                         selected_feed=None,
                         categories=Category.query.all())

@feeds_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_feed():
    categories = Category.query.all()
    if request.method == 'POST':
        feed_url = request.form.get('feed_url')
        category_id = request.form.get('category_id')
        if not feed_url:
            flash('フィードURLを入力してください', 'danger')
            return redirect(url_for('feeds.add_feed'))
        
        
        success, message = add_feed_for_user(feed_url, user_id=current_user.id, category_id=category_id)
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('feeds.dashboard'))
    
    return render_template('add_feed.html', categories=categories)

@feeds_bp.route('/<int:feed_id>/delete', methods=['POST'])
@login_required
def delete_feed(feed_id):
    feed = Feed.query.get_or_404(feed_id)
    
    if feed.user_id != current_user.id:
       flash('このフィードを削除する権限がありません', 'danger')
       return redirect(url_for('feeds.dashboard'))
    
    db.session.delete(feed)
    db.session.commit()
    flash('フィードを削除しました', 'success')
    return redirect(url_for('feeds.dashboard'))

@feeds_bp.route('/update')
@login_required
def update_user_feeds():
    results = update_feeds(user_id=current_user.id)
    for feed_title, message in results:
        flash(f"{feed_title}: {message}", 'info')
    return redirect(url_for('feeds.dashboard'))

@feeds_bp.route('/<int:feed_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_feed(feed_id):
    feed = Feed.query.get_or_404(feed_id)
    
    
    if feed.user_id != current_user.id:
       flash('このフィードを編集する権限がありません', 'danger')
       return redirect(url_for('feeds.dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        if title:
            feed.title = title
            db.session.commit()
            flash('フィードを更新しました', 'success')
            return redirect(url_for('feeds.dashboard'))
    
    return render_template('edit_feed.html', feed=feed)