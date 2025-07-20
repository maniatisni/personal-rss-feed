# Personal RSS Feed

Automated personal RSS feed aggregator that collects articles from your favorite sources and delivers them via email using GitHub Actions and Mailgun.

## Features

- 📰 Aggregates articles from 40+ AI/ML/Tech RSS feeds
- 📧 Automated email delivery via Mailgun
- ⏰ Configurable scheduling (default: daily at 8 AM UTC)
- 🔄 Tracks seen articles to avoid duplicates
- 🎨 Clean HTML email format optimized for readability
- ⚙️ Easy RSS source management via JSON configuration

## Quick Setup

### 1. Fork this repository

### 2. Configure GitHub Secrets
Go to Settings → Secrets and variables → Actions, and add:

- `MAILGUN_API_KEY`: Your Mailgun API key
- `MAILGUN_DOMAIN`: Your Mailgun domain
- `EMAIL_RECIPIENTS`: Email address(es) to receive the digest (comma-separated)

### 3. Enable GitHub Actions
- Go to Actions tab and enable workflows
- The digest will run daily at 8 AM UTC, or trigger manually

### 4. Customize RSS Sources (Optional)
Edit `rss_sources.json` to add/remove RSS feeds or adjust settings:

```json
{
  "feeds": [
    "https://example.com/feed.xml",
    "..."
  ],
  "settings": {
    "article_age_days": 7,
    "seen_articles_file": "seen_articles.json"
  }
}
```

## Local Testing

```bash
# Install dependencies
pip install feedparser requests python-dateutil

# Run the aggregator
python rss_aggregator.py
```

## Customization

### Schedule
Edit `.github/workflows/rss-digest.yml` and modify the cron expression:
```yaml
schedule:
  - cron: '0 8 * * *'  # Daily at 8 AM UTC
```

### Email Template
Modify the HTML styling in `rss_aggregator.py` in the `format_html_output()` function.

### Article Age Filter
Change `article_age_days` in `rss_sources.json` to adjust how far back to look for articles.

## Included RSS Sources

The aggregator monitors 40+ sources including:
- OpenAI, Google AI, Meta Research
- NVIDIA, AWS ML, Microsoft Research
- Hugging Face, MIT News, Berkeley AI
- TechCrunch AI, The Verge AI, Wired AI
- YouTube channels (Two Minute Papers, Lex Fridman, etc.)
- Research publications and AI newsletters

## License

MIT License