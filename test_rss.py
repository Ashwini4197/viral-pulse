import feedparser

feeds = [
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://rss.cnn.com/rss/edition_technology.rss",
    "https://feeds.skynews.com/feeds/rss/technology.xml"
]

for url in feeds:
    feed = feedparser.parse(url)
    print(f"\n✅ {feed.feed.get('title', url)}")
    for entry in feed.entries[:3]:
        print(f"   - {entry.title}")