"""Nạp dữ liệu GIẢ LẬP (nhãn 'simulated') để xem giao diện. KHÔNG phải kết nối thật."""
import time, datetime as dt
from zoneinfo import ZoneInfo
from .channels.simulated import SimulatedChannel


def seed(app):
    z = ZoneInfo("Asia/Ho_Chi_Minh"); db = app.db
    now = time.time(); base = dt.datetime.fromtimestamp(now, z).replace(hour=9, minute=0, second=0, microsecond=0).timestamp() - 86400
    zalo, msn = SimulatedChannel("zalo"), SimulatedChannel("messenger")
    app.adapters.update(zalo=zalo, messenger=msn); app.ing.ai_ext_ids.update(zalo="ai", messenger="ai")
    db.x("INSERT INTO kb_docs(title,body,approved) VALUES('Lịch coaching','Buổi coaching diễn ra mỗi thứ Tư lúc 19:00, kéo dài 45 phút.',1)")
    db.x("INSERT INTO kb_docs(title,body,approved) VALUES('Chính sách hủy lịch (NHÁP)','Hủy lịch trước 24 giờ không mất phí.',0)")
    for ch, ad, gx, nm, code in (("zalo", zalo, "SIM-Z1", "[GIẢ LẬP] Nhóm Zalo A", "KH-001"), ("messenger", msn, "SIM-M1", "[GIẢ LẬP] Nhóm Messenger B", "KH-002")):
        g = app.ing.ensure_group(ch, gx, nm, source="simulated"); db.x("UPDATE groups SET allowed=1, mode='preview', customer_code=? WHERE id=?", code, g["id"])
        for e, n, r in (("kh", "Lan (khách)", "customer"), ("cs", "Hà (CSKH)", "cskh"), ("co", "Minh (coach)", "coach"), ("ai", "Mimi (AI)", "ai")):
            db.x("INSERT INTO members(group_id,ext_id,display_name,role) VALUES(?,?,?,?)", g["id"], e, n, r)
    S = lambda ad, g, who, t, off, **k: ad.inject(g, who, who, t, base + off, **k)
    S(zalo, "SIM-Z1", "kh", "Chị ơi lịch coaching tuần này khi nào ạ?", 0); S(zalo, "SIM-Z1", "cs", "Dạ thứ Tư 19h nhé chị", 300)
    S(zalo, "SIM-Z1", "cs", "Em sẽ gửi tài liệu dinh dưỡng cho chị trong hôm nay", 600)
    S(zalo, "SIM-Z1", "kh", "@Mimi buổi coaching kéo dài bao lâu?", 3600); S(zalo, "SIM-Z1", "kh", "chậm quá, tôi không hài lòng vì chưa nhận được tài liệu", 36000)
    S(msn, "SIM-M1", "kh", "@Mimi cho mình hỏi gói tháng bao nhiêu ạ?", 0); S(msn, "SIM-M1", "ai", "Mình chưa có thông tin giá đã duyệt, mình chuyển người phụ trách nhé.", 60)
    S(msn, "SIM-M1", "kh", "Cảm ơn nhé, mình thấy rất hiệu quả", 7200)
    app.ing.poll(zalo); app.ing.poll(msn); app.resp.tick(now + 100)
