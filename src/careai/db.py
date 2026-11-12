import json, sqlite3, time

SCHEMA = """
CREATE TABLE IF NOT EXISTS groups(
  id INTEGER PRIMARY KEY, channel TEXT NOT NULL, external_id TEXT NOT NULL, name TEXT,
  customer_code TEXT, allowed INTEGER DEFAULT 0, mode TEXT DEFAULT 'off',  -- off|preview|live
  paused INTEGER DEFAULT 0, source TEXT DEFAULT 'real',                   -- real|simulated
  UNIQUE(channel, external_id));
CREATE TABLE IF NOT EXISTS members(
  group_id INTEGER, ext_id TEXT, display_name TEXT, role TEXT DEFAULT 'unknown',
  identity_verified INTEGER DEFAULT 0, address_as TEXT, PRIMARY KEY(group_id, ext_id));
CREATE TABLE IF NOT EXISTS messages(
  id INTEGER PRIMARY KEY, group_id INTEGER, ext_id TEXT, sender_ext TEXT, ts REAL, text TEXT,
  kind TEXT DEFAULT 'text', reply_to_ext TEXT, mentions TEXT DEFAULT '[]',
  is_ai INTEGER DEFAULT 0, trigger INTEGER DEFAULT 0, handled INTEGER DEFAULT 0,
  UNIQUE(group_id, ext_id));
CREATE TABLE IF NOT EXISTS drafts(
  id INTEGER PRIMARY KEY, group_id INTEGER, created REAL, text TEXT, status TEXT,
  trigger_ext TEXT, sources TEXT, flags TEXT, sent_ext TEXT);
CREATE TABLE IF NOT EXISTS commitments(
  id INTEGER PRIMARY KEY, group_id INTEGER, owner_ext TEXT, text TEXT, due_ts REAL,
  status TEXT DEFAULT 'open', evidence_ext TEXT, origin TEXT DEFAULT 'auto', note TEXT);
CREATE TABLE IF NOT EXISTS tasks(
  id INTEGER PRIMARY KEY, group_id INTEGER, title TEXT, assignee TEXT, due_ts REAL,
  status TEXT DEFAULT 'open', created REAL);
CREATE TABLE IF NOT EXISTS kb_docs(
  id INTEGER PRIMARY KEY, title TEXT, body TEXT, approved INTEGER DEFAULT 0, version INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS kb_versions(doc_id INTEGER, version INTEGER, title TEXT, body TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS review_notes(
  id INTEGER PRIMARY KEY, group_id INTEGER, finding_key TEXT, note TEXT, author TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS external_facts(
  id INTEGER PRIMARY KEY, group_id INTEGER, text TEXT, author TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS consent(
  group_id INTEGER, member_ext TEXT, kind TEXT, ts REAL, recorded_by TEXT);
CREATE TABLE IF NOT EXISTS improvements(
  id INTEGER PRIMARY KEY, group_id INTEGER, kind TEXT, detail TEXT, status TEXT DEFAULT 'open', ts REAL);
CREATE TABLE IF NOT EXISTS style_profiles(id INTEGER PRIMARY KEY, name TEXT, body TEXT, version INTEGER DEFAULT 1, approved INTEGER DEFAULT 0, ts REAL);
CREATE TABLE IF NOT EXISTS style_versions(profile_id INTEGER, version INTEGER, body TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS style_examples(id INTEGER PRIMARY KEY, group_id INTEGER, original TEXT, edited TEXT, rule TEXT, status TEXT DEFAULT 'pending', author TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, ts REAL, actor TEXT, action TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS channel_status(channel TEXT PRIMARY KEY, state TEXT, detail TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS outbox_log(idem_key TEXT PRIMARY KEY, group_id INTEGER, ts REAL, text TEXT);
CREATE TABLE IF NOT EXISTS ai_usage(id INTEGER PRIMARY KEY, ts REAL, group_id INTEGER, in_chars INTEGER, out_chars INTEGER, provider TEXT);
"""


class DB:
    def __init__(self, path=":memory:"):
        self.c = sqlite3.connect(path, check_same_thread=False)
        self.c.row_factory = sqlite3.Row
        self.c.executescript(SCHEMA)

    def q(self, sql, *a):
        return [dict(r) for r in self.c.execute(sql, a).fetchall()]

    def one(self, sql, *a):
        r = self.c.execute(sql, a).fetchone()
        return dict(r) if r else None

    def x(self, sql, *a):
        cur = self.c.execute(sql, a)
        self.c.commit()
        return cur.lastrowid

    def audit(self, actor, action, detail=None):
        self.x("INSERT INTO audit(ts,actor,action,detail) VALUES(?,?,?,?)",
               time.time(), actor, action, json.dumps(detail, ensure_ascii=False) if detail is not None else None)

    def get_setting(self, k, default=None):
        r = self.one("SELECT value FROM settings WHERE key=?", k)
        return r["value"] if r else default

    def set_setting(self, k, v):
        self.x("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", k, str(v))
