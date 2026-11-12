"""Giao diện kênh. Mỗi adapter phải khai báo khả năng ĐÃ KIỂM CHỨNG, không phải kỳ vọng."""
from dataclasses import dataclass, field


@dataclass
class InboundMessage:
    channel: str
    group_ext_id: str
    msg_ext_id: str          # id duy nhất phía nền tảng (để khử trùng)
    sender_ext_id: str
    sender_name: str
    ts: float
    text: str
    kind: str = "text"       # text|image|file|voice
    reply_to_ext_id: str = None
    mentions: list = field(default_factory=list)  # ext_id người được mention
    source: str = "real"     # real|simulated


class NotVerified(RuntimeError):
    pass


class ChannelAdapter:
    name = "base"
    # Mọi giá trị mặc định = CHƯA kiểm chứng
    verified = {"receive": False, "history": False, "send": False, "mention": False,
                "reply_detect": False, "media": False}

    def poll(self):            # trả list[InboundMessage]
        raise NotVerified(f"{self.name}: chưa kiểm chứng nhận tin")

    def send(self, group_ext_id, text, idem_key):   # trả msg_ext_id đã gửi
        raise NotVerified(f"{self.name}: chưa kiểm chứng gửi tin")

    def health(self):          # (state, detail) state: ok|degraded|down|unverified
        return ("unverified", "chưa kết nối tài khoản thật")
