import os, sqlite3
from pathlib import Path
from datetime import datetime, timezone
DB_PATH=os.getenv("DB_PATH","database/uno_pro.sqlite3")
def now(): return datetime.now(timezone.utc).isoformat()
def connect():
    Path(DB_PATH).parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c
def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(telegram_id TEXT PRIMARY KEY,username TEXT DEFAULT '',first_name TEXT DEFAULT '',is_banned INTEGER DEFAULT 0,games_played INTEGER DEFAULT 0,wins INTEGER DEFAULT 0,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS games(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id TEXT NOT NULL,status TEXT DEFAULT 'active',winner TEXT DEFAULT '',created_at TEXT NOT NULL,finished_at TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS admins(username TEXT PRIMARY KEY,role TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS admin_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,actor TEXT NOT NULL,action TEXT NOT NULL,target TEXT DEFAULT '',created_at TEXT NOT NULL);
        """)
        c.execute("INSERT OR IGNORE INTO admins VALUES(?,?,?)",(os.getenv("ADMIN_USERNAME","owner"),"owner",now()))
def register_user(uid,username="",first_name=""):
    with connect() as c:
        c.execute("""INSERT INTO users(telegram_id,username,first_name,created_at) VALUES(?,?,?,?)
        ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name""",(str(uid),username or "",first_name or "",now()))
def record_game(uid):
    with connect() as c:
        c.execute("INSERT INTO games(telegram_id,created_at) VALUES(?,?)",(str(uid),now()))
        c.execute("UPDATE users SET games_played=games_played+1 WHERE telegram_id=?",(str(uid),))
def stats():
    with connect() as c:
        return dict(users=c.execute("SELECT COUNT(*) FROM users").fetchone()[0],banned=c.execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0],games=c.execute("SELECT COUNT(*) FROM games").fetchone()[0],active_games=c.execute("SELECT COUNT(*) FROM games WHERE status='active'").fetchone()[0])
def list_users(q=""):
    with connect() as c:
        return [dict(x) for x in c.execute("SELECT * FROM users WHERE telegram_id LIKE ? OR username LIKE ? OR first_name LIKE ? ORDER BY created_at DESC LIMIT 200",(f"%{q}%",)*3)]
def set_banned(uid,banned):
    with connect() as c: return c.execute("UPDATE users SET is_banned=? WHERE telegram_id=?",(int(banned),str(uid))).rowcount>0
def log_action(actor,action,target=""):
    with connect() as c: c.execute("INSERT INTO admin_logs(actor,action,target,created_at) VALUES(?,?,?,?)",(actor,action,str(target),now()))
def logs():
    with connect() as c: return [dict(x) for x in c.execute("SELECT actor,action,target,created_at FROM admin_logs ORDER BY id DESC LIMIT 100")]
def list_admins():
    with connect() as c: return [dict(x) for x in c.execute("SELECT username,role,created_at FROM admins")]
