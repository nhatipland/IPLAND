import json, os
from zoneinfo import ZoneInfo

DEFAULT_STANDARDS = {
    "approved": False,
    "label": "BẢN NHÁP - CHƯA DUYỆT (không dùng xếp hạng nhân viên chính thức)",
    "timezone": "Asia/Ho_Chi_Minh",
    "working_hours": {"mon": [8, 18], "tue": [8, 18], "wed": [8, 18], "thu": [8, 18],
                      "fri": [8, 18], "sat": [8, 12], "sun": None},
    "holidays": [],
    "response_sla_minutes": {"cskh": 30, "coach": 120, "manager": 60},
    "care_schedule_days": {"cskh": 7, "coach": 7},
    "alert_thresholds": {"unanswered_minutes": 60, "overdue_commitments": 1, "complaints": 1},
    "ai": {"debounce_seconds": 20, "max_replies_per_hour": 6, "followup_window_seconds": 120},
}
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def load_standards(path=None):
    s = json.loads(json.dumps(DEFAULT_STANDARDS))
    if path and os.path.exists(path):
        s.update(json.load(open(path, encoding="utf-8")))
    return s


def tz(std):
    return ZoneInfo(std.get("timezone", "Asia/Ho_Chi_Minh"))
