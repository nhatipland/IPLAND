# Kết nối Zalo cá nhân (zca-js) — giai đoạn 1: CHỈ ĐỌC, một nhóm thử

**Trạng thái:** cầu nối đã viết và test phần chuẩn hóa dữ liệu (dữ liệu tổng hợp) + đường đẩy tin vào máy chủ (qua HTTP thật). **Chưa đăng nhập Zalo thật lần nào** (sandbox của tôi bị chặn tới Zalo/Facebook), nên chưa biết nhận được tin thật hay không.

## Chuẩn bị (bạn làm)
1. **Tài khoản trợ lý riêng** (SIM/số riêng), đã được thêm vào **một nhóm thử** chỉ có người trong đội bạn. Không dùng tài khoản nhân viên/khách. Tài khoản này chỉ dành cho AI: hệ thống coi mọi tin do tài khoản này gửi là của AI.
2. Một máy chạy được Node 22 + Python 3.11 (laptop để thử; sau này VPS/máy luôn bật). Chỉ cần cài từ nguồn tin cậy; máy không nên chứa bí mật quan trọng khác.
3. Chấp nhận rủi ro: zca-js là không chính thức; Zalo có thể khóa tài khoản trợ lý. Vì thế dùng tài khoản có thể mất được.

## Chạy
```
# cửa sổ 1: máy chủ quản lý
cd src && CAREAI_ADMIN_TOKEN=<bạn tự đặt> CAREAI_BRIDGE_TOKEN=<chuỗi ngẫu nhiên khác> PYTHONPATH=. python3 -m careai
# cửa sổ 2: cầu nối
cd bridge/zalo && npm ci --ignore-scripts
node bridge.mjs login        # tạo secrets/zalo-qr.png -> quét bằng app Zalo của TÀI KHOẢN TRỢ LÝ, xác nhận trên điện thoại
node bridge.mjs groups       # in "id  tên" các nhóm (KHÔNG đọc nội dung) -> chọn id nhóm thử
CAREAI_BRIDGE_TOKEN=<như trên> ZALO_ALLOWED_GROUPS=<id nhóm thử> node bridge.mjs run
```
Trong giao diện: thêm nhóm (kênh `zalo`, đúng id) → mặc định `mode=off`; đặt `preview`; gán vai trò từng thành viên (khách/CSKH/coach/quản lý).
Phiên đăng nhập nằm ở `secrets/` (đã loại khỏi git, quyền 600). Không gửi tệp này cho ai, không dán vào chat. Phiên hết hạn → cầu nối báo `down` → giao diện có cảnh báo → quét QR lại.

## Phiếu kiểm chứng (điền khi thử thật; chưa ô nào được xác nhận)
| Tiêu chí | Cách thử | Kết quả |
|---|---|---|
| Đúng nhóm/người gửi/nội dung/thời gian | 3 người nhắn trong nhóm thử; so với màn hình `Nhóm`/báo cáo | ☐ |
| Tin văn bản dài, emoji, tiếng Việt có dấu | | ☐ |
| Nhận mention tài khoản trợ lý (`mentions` chứa own id) | @trợ lý trong nhóm | ☐ |
| Nhận "trả lời tin" (trường `quote.globalMsgId` có khớp `msgId` tin gốc?) | reply vào tin cũ | ☐ |
| Ảnh/file/ghi âm: chỉ nhận loại, không nội dung | gửi từng loại | ☐ |
| Tin lịch sử khi cầu nối khởi động | tắt cầu nối, nhắn, bật lại | ☐ (giới hạn lịch sử: chưa biết) |
| Không trùng khi mất mạng/khởi động lại | ngắt Wi-Fi, bật lại | ☐ |
| Tin của nhóm không có trong danh sách bị bỏ | nhắn ở nhóm khác | ☐ |
| Ngắt kết nối → cảnh báo | đăng nhập Zalo Web nơi khác (gây DuplicateConnection) | ☐ |
| **Gửi tin** | *chưa có mã gửi* — chỉ làm sau khi đọc ổn và bạn cho phép | — |
