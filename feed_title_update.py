from app import create_app, db
from app.models import Feed
from urllib.parse import urlparse

app = create_app()

with app.app_context():
    # タイトルが "Feed from" で始まるすべてのフィードを検索
    feeds = Feed.query.filter(Feed.title.like('Feed from %')).all()
    
    for feed in feeds:
        # URLからドメイン名を抽出
        domain = urlparse(feed.url).netloc
        new_title = f"{domain}"
        
        print(f"更新: '{feed.title}' → '{new_title}'")
        feed.title = new_title
    
    # 変更を保存
    db.session.commit()
    print(f"{len(feeds)}件のフィードタイトルを更新しました")