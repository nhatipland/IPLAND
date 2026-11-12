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
