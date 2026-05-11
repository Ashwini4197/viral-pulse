import feedparser
import psycopg2
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    database="viral_pulse",
    user="postgres",
    password="12345"
)
cur = conn.cursor()

# Sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# RSS feeds
feeds = [
    ("technology", "https://feeds.bbci.co.uk/news/technology/rss.xml"),
    ("technology", "https://feeds.skynews.com/feeds/rss/technology.xml"),
    ("business",   "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("world",      "https://feeds.bbci.co.uk/news/world/rss.xml"),
]

total = 0
for subreddit, url in feeds:
    feed = feedparser.parse(url)
    for entry in feed.entries:
        title = entry.get("title", "")
        post_id = entry.get("id", entry.get("link", title))[:20]
        scores = analyzer.polarity_scores(title)
        label = "positive" if scores["compound"] >= 0.05 else "negative" if scores["compound"] <= -0.05 else "neutral"

        try:
            cur.execute("""
                INSERT INTO raw_posts (post_id, source, subreddit, title, created_utc)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (post_id) DO NOTHING
            """, (post_id, "rss", subreddit, title, datetime.utcnow()))

            cur.execute("""
                INSERT INTO sentiment_scores (post_id, compound, positive, negative, neutral, label)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (post_id, scores["compound"], scores["pos"], scores["neg"], scores["neu"], label))

            total += 1
        except Exception as e:
            conn.rollback()
            continue

conn.commit()
cur.close()
conn.close()
print(f"✅ Done! Inserted {total} articles into database.")