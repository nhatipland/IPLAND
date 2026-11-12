"""API quản lý (stdlib). Quản lý = toàn quyền; staff token = xem nhóm + tạm dừng/tiếp tục AI. Chỉ nghe 127.0.0.1 mặc định."""
import json, os, secrets, time, hmac, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .db import DB
from .config import load_standards
from .ingest import Ingest, ROLES
from .responder import Responder, Outbox, get_llm
from .monitor import Monitor
from . import reports


class App:
    def __init__(self, db_path=":memory:", std=None, adapters=None):
        self.db, self.std = DB(db_path), std or load_standards("config/standards.json")
        self.adapters = adapters or {}
        self.ing = Ingest(self.db)
        self.resp = Responder(self.db, self.std, get_llm())
        self.out = Outbox(self.db, self.adapters)
        self.mgr = os.environ.get("CAREAI_ADMIN_TOKEN") or secrets.token_urlsafe(24)
        self.staff = os.environ.get("CAREAI_STAFF_TOKEN") or ""
        self.bridge = os.environ.get("CAREAI_BRIDGE_TOKEN") or ""
        self.hb_timeout = 90

    def role(self, tok):
        if tok and hmac.compare_digest(tok, self.mgr): return "manager"
        if tok and self.staff and hmac.compare_digest(tok, self.staff): return "staff"
        if tok and self.bridge and hmac.compare_digest(tok, self.bridge): return "bridge"
        return None

    def refresh_channels(self):
        self.db.x("UPDATE channel_status SET state='down', detail='mất heartbeat từ cầu nối' WHERE state IN ('ok','degraded') AND ts<?", time.time() - self.hb_timeout)
        for n, a in self.adapters.items():
            st, d = a.health()
            self.db.x("INSERT INTO channel_status(channel,state,detail,ts) VALUES(?,?,?,?) ON CONFLICT(channel) DO UPDATE SET state=excluded.state,detail=excluded.detail,ts=excluded.ts", n, st, d, time.time())

    def handle(self, role, method, path, body):
        db, now = self.db, time.time()
        p = path.rstrip("/").split("/")[2:]   # sau /api
        mgr = role == "manager"
        if role == "bridge":   # cầu nối chỉ được đẩy tin vào và báo nhịp, không đọc/sửa gì khác
            if method == "POST" and p == ["bridge", "heartbeat"]:
                if body["state"] not in ("ok", "down", "degraded"): raise ValueError("state")
                if body.get("own_id"): self.ing.ai_ext_ids[body["channel"]] = str(body["own_id"])
                db.x("INSERT INTO channel_status(channel,state,detail,ts) VALUES(?,?,?,?) ON CONFLICT(channel) DO UPDATE SET state=excluded.state,detail=excluded.detail,ts=excluded.ts",
                     body["channel"], body["state"], str(body.get("detail", ""))[:200], now)
                return {"ok": True}
            if method == "POST" and p == ["bridge", "ingest"]:
                from .channels.base import InboundMessage
                res = {"stored": 0, "duplicate": 0, "dropped_unlisted": 0}
                for m in body["messages"][:200]:
                    sender = self.ing.ai_ext_ids.get(body["channel"]) if m.get("is_self") else m["sender_ext_id"]
                    res[self.ing.handle(InboundMessage(body["channel"], m["group_ext_id"], m["msg_ext_id"], sender, m.get("sender_name", ""),
                                       float(m["ts"]), m.get("text", ""), m.get("kind", "text"), m.get("reply_to_ext_id"), m.get("mentions", []), "real"))] += 1
                return res
            raise PermissionError
        if method == "GET":
            if p == ["status"]:
                self.refresh_channels()
                return dict(role=role, kill_switch=db.get_setting("kill_switch", "0") == "1", channels=db.q("SELECT * FROM channel_status"),
                            standards=dict(approved=self.std["approved"], label=self.std["label"]), llm=self.resp.llm.provider)
            if p == ["groups"]:
                return db.q("SELECT g.*,(SELECT COUNT(*) FROM drafts d WHERE d.group_id=g.id AND d.status='pending') pending FROM groups g")
            if p[:1] == ["members"]: return db.q("SELECT * FROM members WHERE group_id=?", int(p[1]))
            if p[:1] == ["messages"]: return db.q("SELECT m.*,COALESCE(b.display_name,m.sender_ext) name,b.role FROM messages m LEFT JOIN members b ON b.group_id=m.group_id AND b.ext_id=m.sender_ext WHERE m.group_id=? ORDER BY ts", int(p[1]))
            if not mgr: raise PermissionError
            if p == ["report"]: return reports.daily(db, self.std, now)
            if p == ["report.md"]: return {"markdown": reports.to_markdown(reports.daily(db, self.std, now))}
            if p == ["alerts"]: self.refresh_channels(); return reports.alerts(db, self.std, now)
            if p == ["drafts"]: return db.q("SELECT d.*,g.name gname FROM drafts d JOIN groups g ON g.id=d.group_id ORDER BY d.id DESC LIMIT 100")
            if p == ["kb"]: return db.q("SELECT * FROM kb_docs")
            if p == ["tasks"]: return db.q("SELECT t.*,g.name gname FROM tasks t LEFT JOIN groups g ON g.id=t.group_id")
            if p == ["audit"]: return db.q("SELECT * FROM audit ORDER BY id DESC LIMIT 200")
            if p == ["improvements"]: return db.q("SELECT * FROM improvements ORDER BY id DESC LIMIT 100")
            if p == ["style"]: return dict(profiles=db.q("SELECT * FROM style_profiles"), examples=db.q("SELECT * FROM style_examples ORDER BY id DESC LIMIT 100"))
            if p == ["usage"]: return db.one("SELECT COUNT(*) calls, COALESCE(SUM(in_chars),0) in_chars, COALESCE(SUM(out_chars),0) out_chars FROM ai_usage")
            if p[:1] == ["analysis"]: return Monitor(db, self.std).analyze(int(p[1]), now)
        if method == "POST":
            actor = role
            if p == ["group", "pause"] and role:      # staff cũng được tiếp quản
                db.x("UPDATE groups SET paused=? WHERE id=?", int(body["paused"]), body["id"]); db.audit(actor, "pause", body); return {"ok": True}
            if not mgr: raise PermissionError
            if p == ["kill"]: db.set_setting("kill_switch", "1" if body["on"] else "0"); db.audit(actor, "kill_switch", body); return {"ok": True}
            if p == ["group", "update"]:
                if body.get("mode") not in (None, "off", "preview", "live"): raise ValueError("mode")
                for k in ("allowed", "mode", "customer_code", "name"):
                    if k in body: db.x(f"UPDATE groups SET {k}=? WHERE id=?", body[k], body["id"])
                db.audit(actor, "group_update", body); return {"ok": True}
            if p == ["group", "add"]:
                g = self.ing.ensure_group(body["channel"], body["external_id"], body.get("name")); db.x("UPDATE groups SET allowed=1 WHERE id=?", g["id"]); db.audit(actor, "group_add", body); return g
            if p == ["member", "role"]:
                if body["role"] not in ROLES: raise ValueError("role")
                db.x("UPDATE members SET role=? WHERE group_id=? AND ext_id=?", body["role"], body["group_id"], body["ext_id"]); db.audit(actor, "member_role", body); return {"ok": True}
            if p == ["draft", "approve"]: return self.out.approve_and_send(body["id"], actor, body.get("text"))
            if p == ["draft", "reject"]: db.x("UPDATE drafts SET status='rejected' WHERE id=?", body["id"]); db.audit(actor, "draft_reject", body); return {"ok": True}
            if p == ["tick"]: return {"drafts": self.resp.tick(now)}
            if p == ["task"]: i = db.x("INSERT INTO tasks(group_id,title,assignee,due_ts,created) VALUES(?,?,?,?,?)", body.get("group_id"), body["title"], body.get("assignee"), body.get("due_ts"), now); db.audit(actor, "task_create", body); return {"id": i}
            if p == ["task", "status"]: db.x("UPDATE tasks SET status=? WHERE id=?", body["status"], body["id"]); db.audit(actor, "task_status", body); return {"ok": True}
            if p == ["commitment", "status"]: db.x("UPDATE commitments SET status=?, note=? WHERE id=?", body["status"], body.get("note"), body["id"]); db.audit(actor, "commitment_status", body); return {"ok": True}
            if p == ["review_note"]: db.x("INSERT INTO review_notes(group_id,finding_key,note,author,ts) VALUES(?,?,?,?,?)", body["group_id"], body.get("finding_key"), body["note"], actor, now); db.audit(actor, "review_note", body); return {"ok": True}
            if p == ["external_fact"]: db.x("INSERT INTO external_facts(group_id,text,author,ts) VALUES(?,?,?,?)", body["group_id"], body["text"], actor, now); db.audit(actor, "external_fact", body); return {"ok": True}
            if p == ["consent"]: db.x("INSERT INTO consent(group_id,member_ext,kind,ts,recorded_by) VALUES(?,?,?,?,?)", body["group_id"], body["member_ext"], body["kind"], now, actor); db.audit(actor, "consent", body); return {"ok": True}
            if p == ["style", "save"]:
                if body.get("id"):
                    d = db.one("SELECT * FROM style_profiles WHERE id=?", body["id"])
                    db.x("INSERT INTO style_versions VALUES(?,?,?,?)", d["id"], d["version"], d["body"], now)
                    db.x("UPDATE style_profiles SET body=?, version=version+1, approved=0, ts=? WHERE id=?", body["body"], now, d["id"]); i = d["id"]   # sửa => duyệt lại
                else: i = db.x("INSERT INTO style_profiles(name,body,ts) VALUES(?,?,?)", body["name"], body["body"], now)
                db.audit(actor, "style_save", {"id": i}); return {"id": i}
            if p == ["style", "approve"]: db.x("UPDATE style_profiles SET approved=? WHERE id=?", int(body["approved"]), body["id"]); db.audit(actor, "style_approve", body); return {"ok": True}
            if p == ["style", "rollback"]:
                v = db.one("SELECT * FROM style_versions WHERE profile_id=? AND version=?", body["id"], body["version"])
                if not v: raise ValueError("không có phiên bản")
                db.x("UPDATE style_profiles SET body=?, version=version+1, approved=0 WHERE id=?", v["body"], body["id"]); db.audit(actor, "style_rollback", body); return {"ok": True}
            if p == ["style", "example"]:   # xác nhận/bỏ ví dụ + ghi quy tắc rút ra
                if body["status"] not in ("confirmed", "rejected"): raise ValueError("status")
                db.x("UPDATE style_examples SET status=?, rule=? WHERE id=?", body["status"], body.get("rule"), body["id"]); db.audit(actor, "style_example", body); return {"ok": True}
            if p == ["kb", "save"]:
                if body.get("id"):
                    d = db.one("SELECT * FROM kb_docs WHERE id=?", body["id"])
                    db.x("INSERT INTO kb_versions VALUES(?,?,?,?,?)", d["id"], d["version"], d["title"], d["body"], now)
                    db.x("UPDATE kb_docs SET title=?, body=?, version=version+1, approved=0 WHERE id=?", body["title"], body["body"], d["id"]); i = d["id"]   # sửa => phải duyệt lại
                else: i = db.x("INSERT INTO kb_docs(title,body) VALUES(?,?)", body["title"], body["body"])
                db.audit(actor, "kb_save", {"id": i}); return {"id": i}
            if p == ["kb", "approve"]: db.x("UPDATE kb_docs SET approved=? WHERE id=?", int(body["approved"]), body["id"]); db.audit(actor, "kb_approve", body); return {"ok": True}
            if p == ["kb", "rollback"]:
                v = db.one("SELECT * FROM kb_versions WHERE doc_id=? AND version=?", body["id"], body["version"])
                if not v: raise ValueError("không có phiên bản")
                db.x("UPDATE kb_docs SET title=?, body=?, version=version+1, approved=0 WHERE id=?", v["title"], v["body"], body["id"]); db.audit(actor, "kb_rollback", body); return {"ok": True}
        raise LookupError(path)


def make_handler(app):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass     # không log URL/token
        def send_json(self, code, obj):
            b = json.dumps(obj, ensure_ascii=False, default=str).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(b))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(b)
        def do(self, method):
            if self.path in ("/", "/index.html") and method == "GET":
                b = open(os.path.join(os.path.dirname(__file__), "..", "..", "web", "index.html"), "rb").read()
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
            role = app.role((self.headers.get("Authorization") or "").replace("Bearer ", ""))
            if not role: return self.send_json(401, {"error": "cần token"})
            try:
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n)) if n else {}
                self.send_json(200, app.handle(role, method, self.path.split("?")[0], body))
            except PermissionError: self.send_json(403, {"error": "không đủ quyền"})
            except LookupError: self.send_json(404, {"error": "không có"})
            except (KeyError, ValueError, TypeError) as e: self.send_json(400, {"error": f"dữ liệu không hợp lệ: {e}"})
            except Exception as e:
                app.db.audit("system", "api_error", {"path": self.path, "err": type(e).__name__}); self.send_json(500, {"error": type(e).__name__})
        def do_GET(self): self.do("GET")
        def do_POST(self): self.do("POST")
    return H


def serve(app, host="127.0.0.1", port=8765):
    srv = ThreadingHTTPServer((host, port), make_handler(app)); print(f"CareAI quản lý: http://{host}:{port}"); srv.serve_forever()
