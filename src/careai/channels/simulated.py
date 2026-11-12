"""Kênh GIẢ LẬP để thử lõi. Không phải kết nối thật; mọi dữ liệu mang source='simulated'."""
import itertools
from .base import ChannelAdapter, InboundMessage


class SimulatedChannel(ChannelAdapter):
    name = "simulated"
    verified = {k: False for k in ChannelAdapter.verified}   # cố ý: giả lập không chứng minh gì

    def __init__(self, name="simulated"):
        self.name = name
        self.queue, self.sent, self.connected = [], [], True
        self._ids = itertools.count(1)
        self.fail_send_once = False

    def inject(self, group, sender_id, sender_name, text, ts, **kw):
        m = InboundMessage(self.name, group, kw.pop("msg_id", f"sim{next(self._ids)}"), sender_id,
                           sender_name, ts, text, source="simulated", **kw)
        self.queue.append(m)
        return m

    def poll(self):
        if not self.connected:
            raise ConnectionError("mất kết nối (giả lập)")
        out, self.queue = self.queue, []
        return out

    def send(self, group_ext_id, text, idem_key):
        if not self.connected:
            raise ConnectionError("mất kết nối (giả lập)")
        if self.fail_send_once:
            self.fail_send_once = False
            raise TimeoutError("timeout sau khi gửi? (giả lập)")
        mid = f"ai{next(self._ids)}"
        self.sent.append((group_ext_id, text, idem_key, mid))
        return mid

    def health(self):
        return ("ok", "GIẢ LẬP") if self.connected else ("down", "mất kết nối (giả lập)")


class ZaloPersonalAdapter(ChannelAdapter):
    """Khung cho cầu nối zca-js (không chính thức). CHƯA triển khai: chờ người dùng chọn phương án."""
    name = "zalo"


class MessengerAdapter(ChannelAdapter):
    """Khung cho Messenger nhóm cá nhân. CHƯA có đường chính thức; chờ người dùng chọn phương án."""
    name = "messenger"
