-- ai-ltm: SQLite schema for AI long-term memory
-- Run: sqlite3 ~/ai-ltm-data/memory.db < init.sql

CREATE TABLE IF NOT EXISTS episodes (
  id           INTEGER PRIMARY KEY,
  summary      TEXT NOT NULL,
  context      TEXT,
  tags         TEXT,
  embedding    TEXT,     -- JSON object of token:weight (TF-IDF sparse vector)
  used_count   INTEGER DEFAULT 0,
  last_used_at DATETIME,
  archived     INTEGER DEFAULT 0,
  created_at   DATETIME DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(
  summary,
  context,
  tags,
  content='episodes',
  content_rowid='id'
);

-- FTS sync triggers
CREATE TRIGGER IF NOT EXISTS episodes_ai AFTER INSERT ON episodes BEGIN
  INSERT INTO episodes_fts(rowid, summary, context, tags)
  VALUES (new.id, new.summary, new.context, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS episodes_ad AFTER DELETE ON episodes BEGIN
  INSERT INTO episodes_fts(episodes_fts, rowid, summary, context, tags)
  VALUES ('delete', old.id, old.summary, old.context, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS episodes_au AFTER UPDATE ON episodes BEGIN
  INSERT INTO episodes_fts(episodes_fts, rowid, summary, context, tags)
  VALUES ('delete', old.id, old.summary, old.context, old.tags);
  INSERT INTO episodes_fts(rowid, summary, context, tags)
  VALUES (new.id, new.summary, new.context, new.tags);
END;

-- Search tuning parameters
CREATE TABLE IF NOT EXISTS config (
  key   TEXT PRIMARY KEY,
  value TEXT
);

INSERT OR IGNORE INTO config VALUES ('time_decay_days',     '30');
INSERT OR IGNORE INTO config VALUES ('fts_weight',          '0.5');
INSERT OR IGNORE INTO config VALUES ('vector_weight',       '0.5');
INSERT OR IGNORE INTO config VALUES ('usage_boost_weight',  '0.3');
INSERT OR IGNORE INTO config VALUES ('usage_recency_days',  '30');
INSERT OR IGNORE INTO config VALUES ('archive_after_days',  '180');
