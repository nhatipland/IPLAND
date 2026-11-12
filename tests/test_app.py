from careai.app import App
from careai.config import load_standards
from careai.demo import seed
import pytest


def mk():
    a = App(std=load_standards()); a.mgr = "m"; a.staff = "s"; return a


def test_auth_and_roles():
    a = mk(); assert a.role("m") == "manager" and a.role("s") == "staff" and a.role("x") is None and a.role("") is None
    with pytest.raises(PermissionError): a.handle("staff", "GET", "/api/report", {})
    with pytest.raises(PermissionError): a.handle("staff", "POST", "/api/kill", {"on": 1})


def test_demo_seed_and_report_is_labelled_and_private():
    a = mk(); seed(a)
    rep = a.handle("manager", "GET", "/api/report", {})
    assert all(g["source"] == "simulated" for g in rep["groups"]) and "QUẢN LÝ" in rep["audience"]
    kinds = {f["kind"] for g in rep["groups"] for f in g["issues"]}
    assert "complaint" in kinds and "ai_unresolved" in kinds
    assert "CHƯA DUYỆT" in rep["standards_label"]
    assert all(ad.sent == [] for ad in a.adapters.values())      # demo preview: không gửi gì


def test_kb_edit_requires_reapproval_and_rollback():
    a = mk(); i = a.handle("manager", "POST", "/api/kb/save", {"title": "t", "body": "v1"})["id"]
    a.handle("manager", "POST", "/api/kb/approve", {"id": i, "approved": 1})
    a.handle("manager", "POST", "/api/kb/save", {"id": i, "title": "t", "body": "v2"})
    d = a.db.one("SELECT * FROM kb_docs WHERE id=?", i); assert d["approved"] == 0 and d["body"] == "v2"
    a.handle("manager", "POST", "/api/kb/rollback", {"id": i, "version": 1}); assert a.db.one("SELECT body FROM kb_docs WHERE id=?", i)["body"] == "v1"


def test_audit_written_for_sensitive_changes():
    a = mk(); a.handle("manager", "POST", "/api/kill", {"on": 1})
    assert any(r["action"] == "kill_switch" for r in a.db.q("SELECT * FROM audit"))


def test_bridge_role_is_ingest_only_and_logs_nothing_else():
    a = mk(); a.bridge = "b"
    assert a.role("b") == "bridge"
    for m, path in (("GET", "/api/groups"), ("GET", "/api/report"), ("POST", "/api/kill"), ("POST", "/api/group/pause"), ("GET", "/api/messages/1")):
        with pytest.raises(PermissionError): a.handle("bridge", m, path, {"on": 1, "id": 1, "paused": 1})


def test_bridge_ingest_allowlist_dedupe_self_and_heartbeat():
    a = mk(); g = a.handle("manager", "POST", "/api/group/add", {"channel": "zalo", "external_id": "G1", "name": "t"})
    a.handle("bridge", "POST", "/api/bridge/heartbeat", {"channel": "zalo", "state": "ok", "own_id": "OWN"})
    mm = lambda i, **k: dict(group_ext_id="G1", msg_ext_id=i, sender_ext_id="u", ts=1.0, text="hi", **k)
    r = a.handle("bridge", "POST", "/api/bridge/ingest", {"channel": "zalo", "messages": [mm("1"), mm("1"), mm("2", is_self=True), dict(mm("3"), group_ext_id="OTHER")]})
    assert r == {"stored": 2, "duplicate": 1, "dropped_unlisted": 1}
    assert a.db.one("SELECT is_ai FROM messages WHERE ext_id='2'")["is_ai"] == 1 and a.db.one("SELECT is_ai FROM messages WHERE ext_id='1'")["is_ai"] == 0
    assert a.db.one("SELECT source FROM groups WHERE external_id='G1'")["source"] == "real"
    a.hb_timeout = -1; a.refresh_channels()      # mất nhịp -> down -> có cảnh báo
    assert a.db.one("SELECT state FROM channel_status")["state"] == "down"
    assert any(x["kind"] == "channel_down" for x in a.handle("manager", "GET", "/api/alerts", {})["alerts"])


def test_readonly_channel_cannot_send():
    a = mk(); a.handle("manager", "POST", "/api/group/add", {"channel": "zalo", "external_id": "G1", "name": "t"})
    a.db.x("UPDATE groups SET mode='live'"); a.db.x("INSERT INTO drafts(group_id,created,text,status,flags,sources) VALUES(1,1,'x','pending','[]','[]')")
    r = a.handle("manager", "POST", "/api/draft/approve", {"id": 1})
    assert not r["ok"] and "CHỈ ĐỌC" in r["reason"] and a.db.one("SELECT status FROM drafts")["status"] == "approved"
