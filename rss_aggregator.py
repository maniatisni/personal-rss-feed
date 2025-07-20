#!/usr/bin/env python3
"""
RSS Feed Aggregator with Email Delivery

Aggregates articles from multiple RSS feeds, filters for recent content,
and generates HTML email digest.
"""

import feedparser
import requests
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from dateutil import parser
from typing import Dict, List, Set, Tuple, Any


def load_config(config_file: str = "rss_sources.json") -> Dict[str, Any]:
    """Load RSS sources and settings from configuration file."""
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file {config_file} not found")
    
    with open(config_file, 'r') as f:
        return json.load(f)


def load_seen_articles(file_path: str) -> Set[str]:
    """Load the set of seen article URLs from a JSON file."""
    if not os.path.exists(file_path):
        return set()
    
    try:
        with open(file_path, 'r') as f:
            return set(json.load(f))
    except (json.JSONDecodeError, IOError):
        return set()


def save_seen_articles(articles_to_save: Set[str], file_path: str) -> None:
    """Save the updated set of seen article URLs to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(list(articles_to_save), f, indent=2)


def fetch_and_process_feeds(
    feed_urls: List[str], 
    seen_urls: Set[str], 
    article_age_days: int
) -> Tuple[Dict[str, List[Dict[str, Any]]], Set[str], List[str]]:
    """Fetch feeds, filter new and recent articles, and update the seen set."""
    new_articles_by_feed = {}
    failed_feeds = []
    
    # Set a cutoff date for filtering recent articles
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=article_age_days)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'RSS-Feed-Aggregator/1.0 (Python)'
    })

    for url in feed_urls:
        try:
            response = session.get(url, timeout=20)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            feed_title = feed.feed.get('title', 'Untitled Feed')
            new_entries = []

            for entry in feed.entries:
                link = entry.get('link')
                if not link or link in seen_urls:
                    continue

                # Parse publication date
                pub_date_str = entry.get('published', entry.get('updated'))
                if not pub_date_str:
                    continue

                try:
                    pub_date = parser.parse(pub_date_str)
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                    
                    # Check if the article is recent enough
                    if pub_date >= cutoff_date:
                        new_entries.append({
                            'title': entry.get('title', 'No Title'),
                            'link': link,
                            'date': pub_date
                        })
                        seen_urls.add(link)
                except parser.ParserError:
                    continue

            if new_entries:
                # Sort articles by date (newest first)
                new_entries.sort(key=lambda x: x['date'], reverse=True)
                new_articles_by_feed[feed_title] = new_entries

        except requests.RequestException:
            failed_feeds.append(url)
        except Exception:
            failed_feeds.append(url)
            
    return new_articles_by_feed, seen_urls, failed_feeds


def format_html_output(
    new_articles: Dict[str, List[Dict[str, Any]]], 
    failed_feeds: List[str],
    article_age_days: int
) -> str:
    """Format the collected articles into HTML string for email."""
    html = """<!DOCTYPE html>
<html>
<head>
<style>
    body { 
        background-color: #f4f4f4; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
        line-height: 1.6; 
        color: #333; 
        margin: 0; 
        padding: 20px;
    }
    .container { 
        max-width: 800px; 
        margin: 0 auto; 
        padding: 30px; 
        border-radius: 12px; 
        background-color: #ffffff; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
    }
    h1 { 
        color: #1a1a1a; 
        font-size: 26px; 
        border-bottom: 2px solid #eee; 
        padding-bottom: 10px; 
        margin-top: 0;
    }
    h2 { 
        color: #333; 
        font-size: 20px; 
        border-bottom: 1px solid #f0f0f0; 
        padding-bottom: 8px; 
        margin-top: 35px; 
    }
    ul { 
        list-style-type: none; 
        padding-left: 0; 
    }
    li { 
        margin-bottom: 12px; 
        padding: 10px 15px; 
        border-left: 3px solid #007BFF; 
        background-color: #f8f9fa;
        border-radius: 4px;
    }
    .article-date { 
        font-weight: 600; 
        color: #555; 
        margin-right: 8px; 
        font-size: 0.9em;
    }
    a { 
        color: #0056b3; 
        text-decoration: none; 
        font-weight: 500; 
    }
    a:hover { 
        text-decoration: underline; 
    }
    .failed-feeds { 
        margin-top: 40px; 
        padding: 15px; 
        background-color: #fbeaea; 
        border: 1px solid #f5c6cb; 
        border-radius: 8px; 
    }
    .failed-feeds h3 { 
        margin-top: 0; 
        color: #721c24; 
    }
    .summary { 
        background-color: #e7f3ff; 
        padding: 15px; 
        border-radius: 8px; 
        margin-bottom: 20px; 
    }
</style>
</head>
<body>
<div class="container">
"""
    
    # Add header with current date
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    html += f"<h1>RSS Digest - {current_date}</h1>"
    
    if not new_articles:
        html += f'<div class="summary"><p>No new articles found from the last {article_age_days} days.</p></div>'
    else:
        # Add summary
        total_articles = sum(len(articles) for articles in new_articles.values())
        html += f'<div class="summary"><p><strong>{total_articles}</strong> new articles from <strong>{len(new_articles)}</strong> sources in the last {article_age_days} days.</p></div>'
        
        for feed_title, articles in new_articles.items():
            html += f"<h2>{feed_title} ({len(articles)} articles)</h2><ul>"
            for article in articles:
                date_str = article['date'].strftime("%b %d")
                html += f'<li><span class="article-date">{date_str}</span><a href="{article["link"]}" target="_blank">{article["title"]}</a></li>'
            html += "</ul>"

    if failed_feeds:
        html += '<div class="failed-feeds">'
        html += f"<h3>Failed to Fetch ({len(failed_feeds)} feeds)</h3>"
        html += "<p>The following feeds could not be processed:</p><ul>"
        for url in failed_feeds:
            html += f"<li>{url}</li>"
        html += "</ul></div>"

    html += """
</div>
</body>
</html>
"""
    return html


def main():
    """Main execution function."""
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        # Load configuration
        config = load_config()
        feed_urls = config["feeds"]
        settings = config["settings"]
        article_age_days = settings["article_age_days"]
        seen_articles_file = settings["seen_articles_file"]
        
        # Process feeds
        seen_article_urls = load_seen_articles(seen_articles_file)
        new_articles, updated_seen_urls, failures = fetch_and_process_feeds(
            feed_urls, seen_article_urls, article_age_days
        )
        
        # Generate output
        html_output = format_html_output(new_articles, failures, article_age_days)
        save_seen_articles(updated_seen_urls, seen_articles_file)
        
        # Output HTML for email
        print(html_output)
        
        # Optional: Print summary to stderr for logging
        total_articles = sum(len(articles) for articles in new_articles.values())
        print(f"Processed {len(feed_urls)} feeds, found {total_articles} new articles", file=sys.stderr)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()