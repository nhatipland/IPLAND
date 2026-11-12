import sys, os, datetime as dt, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from zoneinfo import ZoneInfo
from careai.db import DB
from careai.config import load_standards
from careai.ingest import Ingest
from careai.responder import Responder, Outbox
from careai.channels.simulated import SimulatedChannel

T0 = dt.datetime(2026, 11, 9, 9, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")).timestamp()  # Thứ Hai 09:00 ICT


class Env:
    def __init__(s):
        s.db, s.std = DB(), load_standards()
        s.ch = SimulatedChannel("zalo")
        s.ing = Ingest(s.db, ai_ext_ids={"zalo": "ai"})
        s.resp = Responder(s.db, s.std)
        s.out = Outbox(s.db, {"zalo": s.ch})
        s.g = s.ing.ensure_group("zalo", "G1", "Nhóm thử A", source="simulated")
        s.db.x("UPDATE groups SET allowed=1, mode='live' WHERE id=?", s.g["id"])
        for ext, name, role in (("kh", "Lan", "customer"), ("cs", "Hà", "cskh"), ("co", "Minh", "coach"), ("ai", "Mimi", "ai")):
            s.db.x("INSERT INTO members(group_id,ext_id,display_name,role) VALUES(?,?,?,?)", s.g["id"], ext, name, role)
        s.db.x("INSERT INTO kb_docs(title,body,approved) VALUES(?,?,1)", "Lịch hẹn coaching", "Buổi coaching diễn ra mỗi thứ Tư lúc 19:00, kéo dài 45 phút.")

    def say(s, who, text, dt_s, **kw):
        s.ch.inject("G1", who, who, text, T0 + dt_s, **kw)
        return s.ing.poll(s.ch)

    def reload(s):
        s.g = s.db.one("SELECT * FROM groups WHERE id=?", s.g["id"])


@pytest.fixture
def env():
    return Env()
