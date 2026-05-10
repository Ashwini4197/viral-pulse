# Power BI Setup Guide — Viral Pulse Dashboard

## Prerequisites
- Power BI Desktop (free download from Microsoft)
- PostgreSQL ODBC driver installed
- Your PostgreSQL database running with data populated

---

## Step 1 — Install PostgreSQL ODBC Driver

Download from: https://www.postgresql.org/ftp/odbc/versions/msi/
Install the `psqlODBC_x64.msi` (64-bit version).

---

## Step 2 — Connect Power BI to PostgreSQL

1. Open **Power BI Desktop**
2. Click **Get Data → PostgreSQL database**
3. Enter:
   - Server: `localhost` (or your server IP)
   - Database: `viral_pulse`
4. Choose **DirectQuery** (for live data — NOT Import)
5. Enter your PostgreSQL username/password

---

## Step 3 — Load the Views

In the Navigator, select these views/tables:

| View/Table | Used On |
|---|---|
| `vw_sentiment_by_hour` | Page 1 — Sentiment |
| `vw_trending_keywords` | Page 2 — Trends |
| `vw_entity_surge` | Page 3 — Entities |
| `daily_summary` | Page 1 (cards) |

Click **Load** → wait for DirectQuery to connect.

---

## Step 4 — Build Page 1: Sentiment Overview

### KPI Cards (top row)
- Visual: **Card**
- Value: `AVG(vw_sentiment_by_hour[avg_sentiment])` → label "Avg Sentiment"
- Add cards for `positive_pct`, `negative_pct`, `total_posts`

### Donut Chart (sentiment split)
- Visual: **Donut chart**
- Legend: Sentiment label (create calculated column: if compound >= 0.05 = "Positive" etc.)
- Values: Count of posts

### Line Chart (sentiment over time)
- Visual: **Line chart**
- X-axis: `hour_bucket`
- Y-axis: `avg_sentiment`
- Legend: `subreddit`
- Filter: Last 7 days

---

## Step 5 — Build Page 2: Trending Topics

### Word Cloud  
- Install **Word Cloud** visual from AppSource (free)
- Category: `keyword`
- Values: `SUM(frequency)`
- Filter: `is_trending = TRUE`

### Bar Chart (top keywords)
- Visual: **Horizontal bar chart**
- Y-axis: `keyword`
- X-axis: `SUM(frequency)`
- Top N filter: 15

### Line Chart (keyword timeline)
- Visual: **Line chart**
- Add a **slicer** for keyword so users can filter by topic
- X: `hour_bucket`, Y: `frequency`

---

## Step 6 — Build Page 3: Entity Intelligence

### Table (entity mentions)
- Columns: `entity_text`, `entity_type`, `SUM(mention_count)`, `AVG(avg_sentiment)`
- Sort: mention_count DESC
- Conditional formatting on avg_sentiment: red = negative, green = positive

### Bar Chart (entity type breakdown)
- Visual: **Stacked bar**
- X: `entity_type`, Y: count, Legend: subreddit

---

## Step 7 — Build Page 4: Trend Alerts

### Alert Table
Use a **custom SQL query** (click "Advanced options" in data source):

```sql
SELECT subreddit, keyword,
       MAX(frequency) AS peak_mentions,
       MAX(spike_ratio) AS spike_ratio,
       MIN(hour_bucket) AS first_detected
FROM vw_trending_keywords
WHERE is_trending = TRUE
  AND hour_bucket >= NOW() - INTERVAL '48 hours'
GROUP BY subreddit, keyword
ORDER BY spike_ratio DESC;
```

### Conditional formatting on spike_ratio:
- > 5x: Red background
- 3–5x: Orange
- 2–3x: Yellow

---

## Step 8 — Set Auto-Refresh

1. **Publish to Power BI Service** (powerbi.com — free account works)
2. Go to Dataset → **Scheduled Refresh**
3. Set to: Every 1 hour
4. Share the dashboard URL with your portfolio/GitHub README

---

## Step 9 — Add to GitHub README

1. Take a screenshot of each dashboard page
2. Record a short GIF using **ScreenToGif** (free tool)
3. Add the GIF at the top of your README
4. Link to the published Power BI report

---

## Pro Tips

- Use **Bookmarks** to create a "snapshot" view vs "last 24 hours" toggle
- Add a **Date Range Slicer** to all pages for interactivity
- Use **Row-Level Security** if you want to demo enterprise features
- Export a `.pbix` file and commit it to your GitHub repo
