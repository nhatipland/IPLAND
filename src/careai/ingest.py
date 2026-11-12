import json, time
from .channels.base import InboundMessage

ROLES = ("customer", "cskh", "coach", "manager", "ai", "unknown")
STAFF = ("cskh", "coach", "manager")


class Ingest:
    """Nhận tin: allowlist -> khử trùng -> bỏ tin của AI -> lưu. Không trả lời ở đây."""

    def __init__(self, db, ai_names=("mimi",), ai_ext_ids=None):
        self.db, self.ai_names = db, [n.lower() for n in ai_names]
        self.ai_ext_ids = ai_ext_ids or {}   # channel -> ext_id của tài khoản AI

    def ensure_group(self, channel, ext_id, name=None, source="real"):
        g = self.db.one("SELECT * FROM groups WHERE channel=? AND external_id=?", channel, ext_id)
        if not g:  # nhóm lạ: ghi nhận nhưng allowed=0 -> sẽ không lưu nội dung
            gid = self.db.x("INSERT INTO groups(channel,external_id,name,source) VALUES(?,?,?,?)",
                            channel, ext_id, name, source)
            g = self.db.one("SELECT * FROM groups WHERE id=?", gid)
        return g

    def is_trigger(self, m, g):
        t = m.text.lower()
        ai_id = self.ai_ext_ids.get(m.channel)
        if ai_id and ai_id in (m.mentions or []):
            return True
        if any(f"@{n}" in t or n in t.split() or t.startswith(n) for n in self.ai_names):
            return True
        if m.reply_to_ext_id:
            r = self.db.one("SELECT is_ai FROM messages WHERE group_id=? AND ext_id=?", g["id"], m.reply_to_ext_id)
            if r and r["is_ai"]:
                return True
        return False

    def handle(self, m: InboundMessage):
        g = self.ensure_group(m.channel, m.group_ext_id, source=m.source)
        if not g["allowed"]:
            self.db.audit("system", "drop_unlisted_group", {"channel": m.channel, "group": m.group_ext_id})
            return "dropped_unlisted"
        if self.db.one("SELECT 1 FROM messages WHERE group_id=? AND ext_id=?", g["id"], m.msg_ext_id):
            return "duplicate"
        is_ai = int(m.sender_ext_id == self.ai_ext_ids.get(m.channel) or
                    bool(self.db.one("SELECT 1 FROM members WHERE group_id=? AND ext_id=? AND role='ai'",
                                     g["id"], m.sender_ext_id)))
        if not self.db.one("SELECT 1 FROM members WHERE group_id=? AND ext_id=?", g["id"], m.sender_ext_id):
            # vai trò chưa biết -> 'unknown'; KHÔNG tự đoán theo tên
            self.db.x("INSERT INTO members(group_id,ext_id,display_name,role) VALUES(?,?,?,?)",
                      g["id"], m.sender_ext_id, m.sender_name, "ai" if is_ai else "unknown")
        trig = 0 if is_ai else int(self.is_trigger(m, g))
        self.db.x("INSERT INTO messages(group_id,ext_id,sender_ext,ts,text,kind,reply_to_ext,mentions,is_ai,trigger,handled)"
                  " VALUES(?,?,?,?,?,?,?,?,?,?,?)", g["id"], m.msg_ext_id, m.sender_ext_id, m.ts, m.text, m.kind,
                  m.reply_to_ext_id, json.dumps(m.mentions), is_ai, trig, 1 if is_ai else 0)
        return "stored"

    def poll(self, adapter):
        res = {"stored": 0, "duplicate": 0, "dropped_unlisted": 0}
        for m in adapter.poll():
            res[self.handle(m)] += 1
        return res
