import feedparser
import time
import logging
from app import db
from app.models import Feed, Article, Category
from config import Config
from datetime import timezone

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def add_feed_for_user(url, user_id, category_id):
    try:
        # フィード数の上限チェック
        user_feeds_count = Feed.query.filter_by(user_id=user_id).count()
        if user_feeds_count >= 15:
            return False, "登録できるフィードは最大15件までです"
            
        parsed = feedparser.parse(url)
        
        feed_title = parsed.feed.get('title', f"Feed from {url}")
                
        feed = Feed(
            title=feed_title[:100],
            url=url,
            user_id=user_id,
            category_id=category_id
        )
        db.session.add(feed)
        db.session.commit()
        
        count = 0
        # Config.MAX_FEED_ENTRIESを使用して記事数を制限
        for entry in parsed.entries[:Config.MAX_FEED_ENTRIES]:
            try:
                logger.debug(f"Processing entry: {entry.get('title', 'No title')}")
                logger.debug(f"Entry type: {type(entry)}")
        
                title = entry.get('title', '').strip()[:200]
                url = (entry.get('link') or entry.get('guid', '')).strip()
                if not title or not url:
                    logger.warning(f"Skipping entry, missing title or URL")
                    continue
                if Article.query.filter_by(url=url, feed_id=feed.id).first():
                    logger.debug(f"Skipping duplicate: {url}")
                    continue
                
                published_date = None
                pub_date = entry.get('pubDate', entry.get('published', entry.get('dc_date', '')))
                if pub_date:
                    try:
                        
                        from email.utils import parsedate_to_datetime
                        try:
                            published_date = parsedate_to_datetime(pub_date)
                        except:
                            # 日付形式が異なる場合、他の形式も試す
                            from dateutil import parser as date_parser
                            try:
                                published_date = date_parser.parse(pub_date)
                                if published_date.tzinfo is None:
                                    published_date = published_date.replace(tzinfo=timezone.utc)
                            except:
                                logger.debug(f"Unable to parse date: {pub_date}")
                    except (ValueError, TypeError, ImportError) as e:
                        logger.debug(f"Invalid date: {pub_date}, Error: {str(e)}")
                elif entry.get('published_parsed'):
                    try:
                        published_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
                    except:
                        logger.debug(f"Invalid published_parsed")
                
                article = Article(
                    title=title,
                    url=url,
                    summary=entry.get('summary', entry.get('description', ''))[:1000],
                    published_date=published_date,
                    feed_id=feed.id
                )
                db.session.add(article)
                count += 1
                logger.debug(f"Added article: {title}")
            except Exception as article_error:
                logger.error(f"Article error: {str(article_error)}")
                continue
        
        try:
            db.session.commit()
            # 古い記事を削除するために新しく追加した関数を呼び出す
            cleanup_old_articles(feed.id)
            logger.info(f"Feed added: {url}, {count} articles")
            return True, f"フィードを追加しました（{count}件の記事を取得）"
        except Exception as commit_error:
            logger.error(f"Commit error: {str(commit_error)}")
            db.session.rollback()
            return False, f"エラー: データベース保存に失敗しました"
    except Exception as e:
            logger.error(f"Feed error: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            db.session.rollback()
            return False, f"エラー: {str(e)}"

def update_feeds(user_id):
    feeds = Feed.query.filter_by(user_id=user_id).all()
    results = []
    for feed in feeds:
        try:
            logger.debug(f"Updating feed: {feed.url} (ID: {feed.id})")
            parsed = feedparser.parse(feed.url)
            logger.debug(f"Feed status: {parsed.get('status', 'N/A')}, Entries: {len(parsed.entries)}")
            if parsed.get('bozo', 0):
                logger.warning(f"Parse error: {parsed.get('bozo_exception', 'Unknown')}")
            new_count = 0
            
            # Config.MAX_FEED_ENTRIESを使用して記事数を制限
            for entry in parsed.entries[:Config.MAX_FEED_ENTRIES]:
                try:
                    title = entry.get('title', '').strip()[:200]
                    url = (entry.get('link') or entry.get('guid', '')).strip()
                    logger.debug(f"Entry - Title: {title}, URL: {url}, GUID: {entry.get('guid', 'N/A')}")
                    if not title or not url:
                        logger.warning(f"Skipping entry, missing title or URL")
                        continue
                    if Article.query.filter_by(url=url, feed_id=feed.id).first():
                        logger.debug(f"Skipping duplicate: {url}")
                        continue
                    
                    # 日付解析部分
                    published_date = None
                    pub_date = entry.get('pubDate', entry.get('published', entry.get('dc_date', '')))
                    if pub_date:
                        try:
                            
                            from email.utils import parsedate_to_datetime
                            try:
                                published_date = parsedate_to_datetime(pub_date)
                            except:
                                # 日付形式が異なる場合、他の形式も試す
                                from dateutil import parser as date_parser
                                try:
                                    published_date = date_parser.parse(pub_date)
                                    if published_date.tzinfo is None:
                                        published_date = published_date.replace(tzinfo=timezone.utc)
                                except:
                                    logger.debug(f"Unable to parse date: {pub_date}")
                        except (ValueError, TypeError, ImportError) as e:
                            logger.debug(f"Invalid date: {pub_date}, Error: {str(e)}")
                    elif entry.get('published_parsed'):
                        try:
                            published_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
                        except:
                            logger.debug(f"Invalid published_parsed")

                    
                    article = Article(
                        title=title,
                        url=url,
                        summary=entry.get('summary', entry.get('description', ''))[:1000],
                        published_date=published_date,
                        feed_id=feed.id
                    )
                    db.session.add(article)
                    new_count += 1
                    logger.debug(f"Added article: {title}")
                except Exception as article_error:
                    logger.error(f"Article error: {str(article_error)}")
                    continue
            
            try:
                db.session.commit()
                # 古い記事を削除する関数を呼び出す
                cleanup_old_articles(feed.id)
                logger.info(f"Updated feed: {feed.url}, {new_count} articles")
                results.append((feed.title, f"更新完了 ({new_count}件の新しい記事)"))
            except Exception as commit_error:
                logger.error(f"Commit error: {str(commit_error)}")
                db.session.rollback()
                results.append((feed.title, f"エラー: データベース保存に失敗しました"))
        except Exception as e:
            logger.error(f"Feed error: {str(e)}")
            results.append((feed.title, f"エラー: {str(e)}"))
    
    return results

def cleanup_old_articles(feed_id, max_entries=None):
    """
    特定のフィードに対して、最新のmax_entries件を超える古い記事を削除
    """
    if max_entries is None:
        max_entries = Config.MAX_FEED_ENTRIES
        
    try:
        # 最新の記事をpublished_dateの降順で取得
        articles = Article.query.filter_by(feed_id=feed_id).order_by(Article.published_date.desc()).all()
        
        # max_entriesより多い場合、古いものを削除
        if len(articles) > max_entries:
            logger.info(f"Cleaning up feed ID {feed_id}: removing {len(articles) - max_entries} old articles")
            for article in articles[max_entries:]:
                db.session.delete(article)
            
            db.session.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Cleanup error for feed {feed_id}: {str(e)}")
        db.session.rollback()
        return False