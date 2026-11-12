import datetime as dt
from .monitor import Monitor
from .config import tz


def daily(db, std, now):
    mon, out = Monitor(db, std), []
    for g in db.q("SELECT * FROM groups WHERE allowed=1"):
        a = mon.analyze(g["id"], now)
        good = [f for f in a["findings"] if f["kind"] == "positive"]
        issues = [f for f in a["findings"] if f["kind"] != "positive"]
        out.append(dict(group=g["name"] or g["external_id"], channel=g["channel"], source=g["source"], customer_code=g["customer_code"],
                        good=good, issues=issues, missing_data=a["missing_data"], stats=a["stats"],
                        open_tasks=db.q("SELECT * FROM tasks WHERE group_id=? AND status!='done'", g["id"]),
                        open_commitments=db.q("SELECT * FROM commitments WHERE group_id=? AND status='open'", g["id"])))
    return dict(date=dt.datetime.fromtimestamp(now, tz(std)).date().isoformat(), standards_label=std["label"] if not std["approved"] else "Chuẩn đã duyệt",
                audience="CHỈ KHU VỰC QUẢN LÝ - không đăng vào nhóm", groups=out)


def to_markdown(rep):
    L = [f"# Báo cáo ngày {rep['date']}", f"_{rep['audience']}_ · {rep['standards_label']}", ""]
    for g in rep["groups"]:
        L += [f"## {g['group']} ({g['channel']}{' · DỮ LIỆU GIẢ LẬP' if g['source']=='simulated' else ''})",
              f"Tin: {g['stats']}", "**Điểm tốt:** " + ("; ".join(f['text'] for f in g['good']) or "chưa ghi nhận")]
        for f in g["issues"]:
            L.append(f"- [{f['type']}/{f['confidence']}] {f['text']} (bằng chứng: {[e.get('ext_id') or e for e in f['evidence']]}) — {f['note']}")
        L += ["**Dữ liệu còn thiếu:** " + ("; ".join(g["missing_data"]) or "không"), ""]
    return "\n".join(L)


def alerts(db, std, now):
    th, mon, out = std["alert_thresholds"], Monitor(db, std), []
    for ch in db.q("SELECT * FROM channel_status WHERE state IN ('down','degraded')"):
        out.append(dict(kind="channel_down", text=f"Kênh {ch['channel']} mất kết nối: {ch['detail']}"))
    for g in db.q("SELECT * FROM groups WHERE allowed=1"):
        a = mon.analyze(g["id"], now)
        n = lambda k: sum(1 for f in a["findings"] if f["kind"] == k)
        if n("complaint") >= th["complaints"]: out.append(dict(kind="complaint", group=g["name"], text="Có dấu hiệu phàn nàn"))
        if n("overdue_commitment") >= th["overdue_commitments"]: out.append(dict(kind="overdue", group=g["name"], text="Có cam kết quá hạn"))
        if n("unanswered"): out.append(dict(kind="unanswered", group=g["name"], text="Có câu hỏi chưa thấy nhân viên trả lời"))
    return dict(alerts=out, standards_approved=std["approved"])
