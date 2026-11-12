# Messenger cá nhân — thẩm định thư viện trước khi dùng (2026-11-12)

Không có đường chính thức cho nhóm Messenger thường. Các thư viện không chính thức là **fork ẩn danh** của `facebook-chat-api` (bản gốc đã lưu trữ từ 07/2022, [GitHub](https://github.com/Schmavery/facebook-chat-api)). Đăng nhập bằng **appState = cookie phiên Facebook** — tương đương mật khẩu đã đăng nhập: lộ là mất tài khoản.

**Quét sơ bộ `biar-fca@3.9.5`** (tải gói npm về đọc, KHÔNG chạy, KHÔNG phải kiểm toán bảo mật):
- 1 người duy trì (ẩn danh), phát hành cuối 2026-03-13 (~8 tháng trước). Kho: github.com/Jubiar01/biar-fca. Không có `postinstall`.
- Chỉ thấy tên miền Facebook/Messenger trong mã (không thấy máy chủ lạ). Các `exec` tìm thấy là regex, không phải `child_process`.
- Điều đáng ngờ/không cần thiết cho thư viện chat: phụ thuộc `express`, `faker`, `node-cron`, `freeport` (có thể mở cổng cục bộ/giả lập trình duyệt). Chưa đọc hết 70 tệp, chưa theo dõi mạng khi chạy.

**Khuyến nghị:** (1) dùng **tài khoản Facebook thử nghiệm** có nhóm thử, không phải tài khoản thật của bạn/nhân viên; (2) chạy trong container/máy riêng không chứa bí mật khác, ghim phiên bản, `npm ci --ignore-scripts`; (3) tôi chưa viết cầu nối Messenger vì **chưa biết chính xác dạng sự kiện** (README kiểu fork ghi `listenMqtt` với `threadID/senderID/body/messageID`, chưa xác nhận cho nhóm, mention, reply). Khi bạn đồng ý các điều trên, tôi viết cầu nối cùng giao thức `/api/bridge/*` như Zalo (máy chủ đã sẵn sàng nhận kênh `messenger`).
- Rủi ro khác: Meta có thể khóa/yêu cầu xác minh (checkpoint) tài khoản; thư viện có thể hỏng bất cứ lúc nào khi Facebook đổi.
