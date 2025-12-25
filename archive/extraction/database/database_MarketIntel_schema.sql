-- id: 20251201_database_marketintel_schema
-- type: schema
-- subject: database
-- description: "SQLite schema extracted from MarketIntel repo - 12 tables for market research"
-- created_at: 2025-12-01
-- updated_at: 2025-12-01
-- tags: [database, sqlite, schema, marketintel, extraction]

-- =============================================================================
-- MarketIntel Database Schema
-- =============================================================================
-- Source: idkny/MarketIntel
-- Production Data: 1346 keywords, 1997 businesses, 427 sessions
-- =============================================================================

-- CORE TABLES

CREATE TABLE IF NOT EXISTS Keywords (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_text TEXT NOT NULL UNIQUE,
    initial_category TEXT,
    source_endpoint TEXT,
    base_query TEXT,
    predicted_category TEXT,
    confidence_score REAL,
    status TEXT DEFAULT 'pending_review',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT,
    state TEXT,
    country TEXT,
    uule_code TEXT,
    population INTEGER,
    UNIQUE(city, state, country)
);

CREATE TABLE IF NOT EXISTS SearchSessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    engine_used TEXT,
    device_type TEXT,
    serpapi_id TEXT,
    session_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (keyword_id) REFERENCES Keywords (keyword_id),
    FOREIGN KEY (location_id) REFERENCES Locations (location_id)
);

-- RESULT TABLES (linked via session_id)

CREATE TABLE IF NOT EXISTS OrganicResults (
    organic_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    position INTEGER,
    title TEXT,
    url TEXT,
    domain TEXT,
    snippet TEXT,
    date_published TIMESTAMP,
    content_type TEXT,
    search_intent_classified TEXT,
    site_category_classified TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions (session_id)
);

CREATE TABLE IF NOT EXISTS PaidAds (
    paid_ad_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    position INTEGER,
    title TEXT,
    link TEXT,
    displayed_link TEXT,
    snippet TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions (session_id)
);

CREATE TABLE IF NOT EXISTS LocalBusinessResults (
    local_business_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    business_name TEXT,
    address TEXT,
    phone TEXT,
    website TEXT,
    google_maps_link TEXT,
    rating REAL,
    total_reviews INTEGER,
    category TEXT,
    place_id TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions (session_id)
);

CREATE TABLE IF NOT EXISTS RelatedQuestions (
    related_question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question_text TEXT,
    answer_snippet TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions (session_id)
);

CREATE TABLE IF NOT EXISTS NewsArticles (
    news_article_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    title TEXT,
    url TEXT,
    source TEXT,
    published_date TIMESTAMP,
    snippet TEXT,
    relevance_score REAL,
    FOREIGN KEY (session_id) REFERENCES SearchSessions (session_id)
);

-- ANALYTICS TABLES

CREATE TABLE IF NOT EXISTS GoogleTrendsData (
    google_trends_data_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    date_range_query TEXT,
    data_type TEXT,
    interest_value INTEGER,
    trending_topic_or_query_text TEXT,
    extracted_value TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (keyword_id) REFERENCES Keywords (keyword_id),
    FOREIGN KEY (location_id) REFERENCES Locations (location_id)
);

CREATE TABLE IF NOT EXISTS Entities (
    entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_id INTEGER,
    source_table TEXT,
    entity_text TEXT,
    salience REAL,
    sentiment_score REAL,
    sentiment_magnitude REAL,
    num_mentions INTEGER,
    entity_type TEXT
);

-- CACHING & LOGGING TABLES (HIGH VALUE FOR AUTOBIZ)

CREATE TABLE IF NOT EXISTS cache (
    key TEXT PRIMARY KEY,
    engine TEXT,
    params_json TEXT,
    response_json TEXT,
    fetched_at REAL,
    ttl_seconds INTEGER
);

CREATE TABLE IF NOT EXISTS harvest_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    params_json TEXT NOT NULL,
    response_json TEXT,
    saved_to TEXT,
    status TEXT NOT NULL,
    http_status INTEGER,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
