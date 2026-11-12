"""Giám sát chất lượng. Mọi nhận xét: bằng chứng + mức chắc chắn + loại (fact/inference/suggestion) + dữ liệu thiếu.
Không xếp hạng, không chấm điểm nhân viên. AI không bao giờ được tính là nhân viên đã xử lý."""
import re, datetime as dt
from .config import tz, DAYS
from .ingest import STAFF

Q_RE = re.compile(r"(\?|\bkhông ạ\b|\bbao nhiêu\b|\bkhi nào\b|\bnhư thế nào\b|\bthế nào\b|\blàm sao\b|\bđược không\b|\bnhờ\b)", re.I)
COMMIT_RE = re.compile(r"(em|mình|anh|chị|coach|bên em)\s*(sẽ|để em|để mình|xin phép)\s+(gửi|đặt|xếp|check|kiểm tra|gọi|nhắn|phản hồi|cập nhật)[^.\n]*", re.I)
DONE_RE = re.compile(r"\b(đã gửi|gửi rồi|xong rồi|đã xong|đã đặt|đã cập nhật|đã gọi)\b", re.I)
COMPLAIN_RE = re.compile(r"(không hài lòng|phàn nàn|bực|tệ quá|chậm quá|thất vọng|không ai trả lời|bị bỏ rơi)", re.I)
HAPPY_RE = re.compile(r"(cảm ơn|hài lòng|tuyệt|rất tốt|hiệu quả)", re.I)
CONFUSED_RE = re.compile(r"(không hiểu|chưa hiểu|là sao|khó hiểu|nghĩa là gì)", re.I)
STOP_RE = re.compile(r"(muốn dừng|ngừng|hủy|không tiếp tục)", re.I)


def _wh(std, d):
    return std["working_hours"].get(DAYS[d.weekday()])


def working_seconds(std, a, b):
    """Số giây trong giờ làm việc giữa epoch a..b (múi giờ cấu hình, trừ ngày nghỉ)."""
    if b <= a: return 0
    z = tz(std); A, B = dt.datetime.fromtimestamp(a, z), dt.datetime.fromtimestamp(b, z)
    total, day = 0, A.date()
    while day <= B.date():
        wh = _wh(std, dt.datetime.combine(day, dt.time(), z))
        if wh and day.isoformat() not in std["holidays"]:
            s = dt.datetime.combine(day, dt.time(wh[0]), z); e = dt.datetime.combine(day, dt.time(wh[1]), z)
            lo, hi = max(s, A), min(e, B)
            if hi > lo: total += (hi - lo).total_seconds()
        day += dt.timedelta(days=1)
    return total


def due_from_text(text, base_ts, std):
    z = tz(std); d = dt.datetime.fromtimestamp(base_ts, z); t = text.lower()
    if "ngày mai" in t or "mai" in t.split(): d += dt.timedelta(days=1)
    elif not re.search(r"hôm nay|tối nay|chiều nay|sáng nay|trong ngày", t): return None
    return dt.datetime.combine(d.date(), dt.time(23, 59), z).timestamp()


class Monitor:
    def __init__(self, db, std):
        self.db, self.std = db, std

    def roles(self, gid):
        return {m["ext_id"]: m for m in self.db.q("SELECT * FROM members WHERE group_id=?", gid)}

    def scan_commitments(self, gid):
        """Phát hiện cam kết của NHÂN VIÊN (không phải AI) và gắn bằng chứng."""
        roles = self.roles(gid)
        for m in self.db.q("SELECT * FROM messages WHERE group_id=? AND is_ai=0 ORDER BY ts", gid):
            if roles.get(m["sender_ext"], {}).get("role") not in STAFF: continue
            mt = COMMIT_RE.search(m["text"])
            if mt and not self.db.one("SELECT 1 FROM commitments WHERE group_id=? AND evidence_ext=?", gid, m["ext_id"]):
                self.db.x("INSERT INTO commitments(group_id,owner_ext,text,due_ts,evidence_ext) VALUES(?,?,?,?,?)",
                          gid, m["sender_ext"], mt.group(0).strip(), due_from_text(m["text"], m["ts"], self.std), m["ext_id"])

    def analyze(self, gid, now):
        self.scan_commitments(gid)
        std, roles = self.std, self.roles(gid)
        msgs = self.db.q("SELECT * FROM messages WHERE group_id=? ORDER BY ts", gid)
        isstaff = lambda m: (not m["is_ai"]) and roles.get(m["sender_ext"], {}).get("role") in STAFF
        iscust = lambda m: (not m["is_ai"]) and roles.get(m["sender_ext"], {}).get("role") == "customer"
        F, missing = [], []
        unknown = [r["display_name"] for r in roles.values() if r["role"] == "unknown"]
        if unknown: missing.append(f"Chưa gán vai trò cho: {', '.join(unknown)} — tin của họ không được tính vào đánh giá.")
        if self.db.q("SELECT 1 FROM external_facts WHERE group_id=?", gid) == []:
            missing.append("Chưa có kết quả cuộc gọi/công việc ngoài nhóm do quản lý bổ sung.")
        sla = std["response_sla_minutes"]
        for i, m in enumerate(msgs):
            if not iscust(m) or not Q_RE.search(m["text"]): continue
            # chỉ xét câu hỏi đầu của một cụm; bỏ qua nếu có tin khách sau trong 2 phút (cụm liên tiếp)
            reply = next((x for x in msgs[i + 1:] if isstaff(x)), None)
            ai_reply = next((x for x in msgs[i + 1:] if x["is_ai"] and (not reply or x["ts"] < reply["ts"])), None)
            ev = [{"ext_id": m["ext_id"], "ts": m["ts"], "text": m["text"]}]
            if reply:
                sec = working_seconds(std, m["ts"], reply["ts"]); ev.append({"ext_id": reply["ext_id"], "ts": reply["ts"], "text": reply["text"]})
                rr = roles[reply["sender_ext"]]["role"]
                if sec / 60 > sla.get(rr, 60):
                    F.append(dict(kind="slow_response", type="fact", confidence="high",
                                  text=f"Câu hỏi được {rr} trả lời sau {sec/60:.0f} phút làm việc (chuẩn nháp {sla.get(rr)} phút).",
                                  evidence=ev, note="Có thể đã trao đổi ngoài nhóm — quản lý bổ sung nếu có."))
            else:
                sec = working_seconds(std, m["ts"], now)
                if sec / 60 > std["alert_thresholds"]["unanswered_minutes"]:
                    F.append(dict(kind="unanswered", type="fact", confidence="medium",
                                  text=f"Chưa thấy nhân viên trả lời trong nhóm sau {sec/60:.0f} phút làm việc."
                                       + (" AI đã trả lời nhưng không tính là nhân viên xử lý." if ai_reply else ""),
                                  evidence=ev, note="Chưa thấy trong chat ≠ chắc chắn chưa xử lý."))
        for c in self.db.q("SELECT * FROM commitments WHERE group_id=?", gid):
            later = [x for x in msgs if x["ts"] > next((y["ts"] for y in msgs if y["ext_id"] == c["evidence_ext"]), 0)
                     and isstaff(x) and x["sender_ext"] == c["owner_ext"] and DONE_RE.search(x["text"])]
            if c["status"] == "open" and later:
                self.db.x("UPDATE commitments SET status='seen_done' WHERE id=?", c["id"]); c["status"] = "seen_done"
            if c["status"] == "open" and c["due_ts"] and now > c["due_ts"]:
                F.append(dict(kind="overdue_commitment", type="inference", confidence="medium",
                              text=f"Cam kết \"{c['text']}\" quá hạn, chưa thấy bằng chứng hoàn thành trong chat.",
                              evidence=[{"ext_id": c["evidence_ext"]}], note="Quản lý có thể đánh dấu hoàn thành nếu làm ngoài nhóm."))
        for m in msgs:
            if not iscust(m): continue
            for rx, kind, txt in ((COMPLAIN_RE, "complaint", "Khách có dấu hiệu phàn nàn"), (CONFUSED_RE, "confused", "Khách có vẻ chưa hiểu"),
                                  (STOP_RE, "wants_stop", "Khách có thể muốn dừng dịch vụ"), (HAPPY_RE, "positive", "Khách bày tỏ hài lòng")):
                if rx.search(m["text"]) and not (kind == "positive" and (COMPLAIN_RE.search(m["text"]) or re.search(r"không (hài lòng|hiệu quả|tốt)", m["text"], re.I))):
                    F.append(dict(kind=kind, type="inference", confidence="low", text=txt + " (dựa trên từ khóa; có thể là nói đùa/ngữ cảnh khác).",
                                  evidence=[{"ext_id": m["ext_id"], "ts": m["ts"], "text": m["text"]}], note="Cần người xem lại."))
        ai_issues = [d for d in self.db.q("SELECT * FROM drafts WHERE group_id=?", gid) if "handoff" in d["flags"] or "claims_action_done" in d["flags"]]
        if ai_issues:
            F.append(dict(kind="ai_unresolved", type="fact", confidence="high", text=f"AI chuyển người phụ trách {len(ai_issues)} lần (lỗi/giới hạn của AI, tách khỏi đánh giá nhân viên).",
                          evidence=[{"draft": d["id"]} for d in ai_issues], note=""))
        silence = [] if msgs else ["Chưa có tin nhắn."]
        return dict(group_id=gid, findings=F, missing_data=missing + silence,
                    stats=dict(total=len(msgs), customer=sum(map(iscust, msgs)), staff=sum(map(isstaff, msgs)), ai=sum(1 for m in msgs if m["is_ai"])),
                    standards_approved=std["approved"], standards_label=std["label"] if not std["approved"] else "Chuẩn đã duyệt",
                    caveat="Không phải xếp hạng nhân viên. Im lặng/ít tin nhắn không bị coi là dấu hiệu xấu.")
