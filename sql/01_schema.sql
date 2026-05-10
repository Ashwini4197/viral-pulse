-- =============================================================
--  VIRAL PULSE — Database Schema
--  Run: psql -U postgres -d viral_pulse -f sql/01_schema.sql
-- =============================================================

CREATE DATABASE IF NOT EXISTS viral_pulse;

-- -----------------------------------------------
-- Table 1: raw_posts
-- Stores every post pulled from Reddit/RSS
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS raw_posts (
    id              SERIAL PRIMARY KEY,
    post_id         VARCHAR(20) UNIQUE NOT NULL,   -- Reddit post ID
    source          VARCHAR(20) NOT NULL,           -- 'reddit' or 'rss'
    subreddit       VARCHAR(100),
    title           TEXT NOT NULL,
    body            TEXT,
    author          VARCHAR(100),
    url             TEXT,
    score           INTEGER DEFAULT 0,             -- Reddit upvotes
    num_comments    INTEGER DEFAULT 0,
    created_utc     TIMESTAMP NOT NULL,
    collected_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_raw_posts_created   ON raw_posts(created_utc DESC);
CREATE INDEX idx_raw_posts_subreddit ON raw_posts(subreddit);

-- -----------------------------------------------
-- Table 2: sentiment_scores
-- VADER sentiment for each post
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS sentiment_scores (
    id              SERIAL PRIMARY KEY,
    post_id         VARCHAR(20) REFERENCES raw_posts(post_id) ON DELETE CASCADE,
    compound        FLOAT NOT NULL,   -- -1.0 (most negative) to +1.0 (most positive)
    positive        FLOAT NOT NULL,
    negative        FLOAT NOT NULL,
    neutral         FLOAT NOT NULL,
    label           VARCHAR(10) NOT NULL,   -- 'positive', 'negative', 'neutral'
    scored_at       TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sentiment_post_id ON sentiment_scores(post_id);
CREATE INDEX idx_sentiment_label   ON sentiment_scores(label);

-- -----------------------------------------------
-- Table 3: extracted_entities
-- Named entities (brands, people, orgs) per post
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS extracted_entities (
    id              SERIAL PRIMARY KEY,
    post_id         VARCHAR(20) REFERENCES raw_posts(post_id) ON DELETE CASCADE,
    entity_text     VARCHAR(255) NOT NULL,
    entity_type     VARCHAR(20) NOT NULL,   -- 'ORG', 'PERSON', 'PRODUCT', 'GPE'
    mention_count   INTEGER DEFAULT 1,
    extracted_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_entities_text ON extracted_entities(entity_text);
CREATE INDEX idx_entities_type ON extracted_entities(entity_type);

-- -----------------------------------------------
-- Table 4: keyword_trends
-- TF-IDF top keywords per subreddit per hour
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS keyword_trends (
    id              SERIAL PRIMARY KEY,
    subreddit       VARCHAR(100) NOT NULL,
    keyword         VARCHAR(255) NOT NULL,
    hour_bucket     TIMESTAMP NOT NULL,   -- Truncated to the hour
    frequency       INTEGER NOT NULL,
    tfidf_score     FLOAT,
    is_trending     BOOLEAN DEFAULT FALSE,   -- TRUE if >2x 7-day avg
    recorded_at     TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_keywords_subreddit ON keyword_trends(subreddit);
CREATE INDEX idx_keywords_bucket    ON keyword_trends(hour_bucket DESC);
CREATE INDEX idx_keywords_trending  ON keyword_trends(is_trending) WHERE is_trending = TRUE;

-- -----------------------------------------------
-- Table 5: daily_summary (materialized daily)
-- Pre-aggregated stats for Power BI performance
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS daily_summary (
    id              SERIAL PRIMARY KEY,
    summary_date    DATE NOT NULL,
    subreddit       VARCHAR(100),
    total_posts     INTEGER DEFAULT 0,
    avg_sentiment   FLOAT,
    positive_pct    FLOAT,
    negative_pct    FLOAT,
    neutral_pct     FLOAT,
    top_entity      VARCHAR(255),
    top_keyword     VARCHAR(255),
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(summary_date, subreddit)
);
