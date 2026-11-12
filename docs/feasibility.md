# Bảng khả thi Zalo & Messenger (kiểm tra ngày 2026-11-12)

**Mức kiểm chứng:** 🟥 chưa thử thực tế · 🟨 tài liệu/nguồn thứ cấp có mô tả · 🟩 đã chạy thật.
**Hiện tại KHÔNG có ô nào 🟩**: chưa kết nối tài khoản thật nào. Nguồn dưới đây chủ yếu là kết quả tìm kiếm web (tài liệu bên thứ ba, README gói npm); **tôi chưa đọc trực tiếp trang developers.zalo.me hay tài liệu Messenger gốc đầy đủ** → mọi kết luận cần được xác nhận ở bước thử thật.

## Zalo (nhóm thường, tài khoản cá nhân tham gia)

| Phương án | Điều đã biết (nguồn) | Mức | Nhận xét |
|---|---|---|---|
| **Zalo OA / Zalo Bot Platform (chính thức)** | Bot API có `chatId`; với nhóm thì chatId là group ID ([zalo-bot-js](https://kaiyodev.github.io/zalo-bot-js/en/send-message), [chat-sdk](https://chat-sdk.dev/adapters/zalo) ghi nhóm "Pending"). Tài liệu OpenClaw nói bot Zalo thực tế **không thêm được vào nhóm** ([docs.openclaw.ai/channels/zalo](https://docs.openclaw.ai/channels/zalo)). SDK cộng đồng có "Group Message Framework" cho nhóm do OA/asset quản lý ([redai-zalo-sdk](https://unpkg.com/@warriorteam/redai-zalo-sdk@1.39.2/README.md)). | 🟨 (mâu thuẫn) | Có vẻ **không áp dụng cho nhóm Zalo thường hiện có**. Đây là hộp thư OA/nhóm kiểu khác → **không tự thay thế**; nếu muốn, cần bạn quyết định (khác biệt: khách phải theo dõi OA, nhóm do OA tạo, mất nhóm cũ). |
| **Thư viện không chính thức `zca-js`** (MIT, mô phỏng Zalo Web, đăng nhập QR) | README: dành cho tài khoản cá nhân, **cảnh báo có thể bị khóa/cấm tài khoản** ([github.com/RFS-ADRENO/zca-js](https://github.com/RFS-ADRENO/zca-js), [npm](https://npmjs.com/package/zca-js)). Một danh sách ghi push cuối 05/2025 — **chưa kiểm tra bảo trì hiện tại**. OpenClaw có plugin dùng nó và cũng cảnh báo rủi ro cấm ([docs](https://docs.openclaw.ai/channels/zalouser.md)). | 🟨 | Là đường **duy nhất nghe có thể đọc/gửi trong nhóm thường**. Rủi ro: khóa tài khoản, API đổi bất ngờ, không có SLA. Chưa có điều khoản Zalo cấm/cho phép rõ (không tìm thấy điều khoản gốc về tự động hóa) → cần đọc điều khoản hiện hành. |
| **Tự động hóa giao diện (Android/emulator + Accessibility)** | Chưa nghiên cứu nguồn riêng. | 🟥 giả định | Chậm, dễ vỡ khi app cập nhật, khó đọc ảnh/ghi âm, cần thiết bị chạy 24/7; rủi ro điều khoản tương tự. Dự phòng cuối. |
| **Chế độ chỉ-thủ-công** (CSKH dán đoạn chat vào hệ thống/xuất chat) | Không phụ thuộc nền tảng. | 🟩 (tự nhiên) | Không tự động, nhưng **giám sát chất lượng (chức năng B) vẫn dùng được** và rủi ro tài khoản bằng 0. |

Số điện thoại/tài khoản: zca-js đăng nhập bằng QR từ **một tài khoản Zalo cá nhân đã nằm trong nhóm**. Khuyến nghị tài khoản riêng của "trợ lý" (cần SIM/số riêng — *giả định*; dùng tài khoản của nhân viên thật sẽ nhập nhằng danh tính và rủi ro cao hơn). Cần máy chạy thường trực (tiến trình giữ kết nối) — 🟨. Phiên hết hạn: phải quét QR lại bởi người; hệ thống phát cảnh báo ngắt kết nối (đã có cơ chế trạng thái kênh, chưa thử thật).
Nhận tin mới/lịch sử/ảnh/file/ghi âm/mention/reply/gửi: **chưa biết — 🟥 phải thử** (README liệt kê API nghe/gửi nhưng khả năng thực tế theo từng loại tin chưa kiểm chứng).

## Messenger (nhóm thường, tài khoản cá nhân tham gia)

| Phương án | Điều đã biết | Mức | Nhận xét |
|---|---|---|---|
| **Messenger Platform chính thức (Graph API)** | Tài liệu Meta mô tả nền tảng dành cho **Trang (Page)/Instagram Professional** trả lời người nhắn tới; User ID đăng nhập Facebook "không dành cho Send/Receive API" ([overview](https://developers.facebook.com/documentation/business-messaging/messenger-platform/overview), [FAQ](https://developers.facebook.com/docs/messenger-platform/faq)). Bên thứ ba nói bot không vào nhóm chat cá nhân ([messengerbot.app](https://messengerbot.app/?p=259349), nguồn thứ cấp). Workplace có bot nhóm nhưng là sản phẩm khác ([docs](https://developers.facebook.com/docs/workplace/bots)). | 🟨 | **Không tìm thấy đường chính thức** cho nhóm Messenger thường. Fanpage Inbox là kênh khác (1-1 khách↔Page) → **không tự thay thế**. |
| **Thư viện không chính thức (kiểu fca/MQTT)** | Tìm kiếm không cho ra nguồn đáng tin về tình trạng bảo trì/ban. | 🟥 chưa nghiên cứu đủ | Rủi ro cao theo bản chất (đăng nhập tài khoản cá nhân bằng giao thức phản kỹ thuật, Meta chống bot, checkpoint). **Không khuyến nghị cho khách thật** trước khi có bằng chứng; nếu thử, chỉ với tài khoản thử nghiệm của bạn, nhóm thử. |
| **Tự động hóa giao diện (Messenger web/app)** | Chưa nghiên cứu nguồn riêng. | 🟥 giả định | Như Zalo; thêm xác minh 2 bước/checkpoint. |
| **Chế độ chỉ-thủ-công** | — | 🟩 | Như trên. |

**Điểm bị chặn:** chưa có phương án *chính thức* cho cả hai loại nhóm thường. Mọi phương án tự động đọc/gửi đều là không chính thức và có rủi ro tài khoản — quyết định của bạn.

## Chi phí
- **Đã biết:** zca-js miễn phí (MIT); lõi này dùng stdlib Python, không phí cấp phép.
- **Giả định (chưa xác minh):** máy/VPS nhỏ chạy thường trực; số/SIM riêng cho tài khoản trợ lý; chi phí mô hình AI = (số lượt trả lời/tháng) × (token vào+ra) × đơn giá hiện hành của nhà cung cấp. Công thức theo mức dùng: xem `docs/operations.md` §Chi phí. Tôi **không ghi đơn giá** vì chưa kiểm tra bảng giá hiện hành.

## Cần bạn chọn (gộp)
1. Zalo: (a) thử `zca-js` với tài khoản trợ lý riêng + **một nhóm thử** · (b) chỉ-thủ-công · (c) khảo sát OA/GMF (khác biệt lớn, cần chuyển nhóm).
2. Messenger: (a) chỉ-thủ-công (khuyến nghị tới khi có bằng chứng) · (b) thử không chính thức với tài khoản/nhóm thử · (c) khảo sát Fanpage Inbox (đổi kênh).
3. Ai có quyền: danh sách nhóm được phép, tên/biệt danh trợ lý, kênh nhận báo cáo (khu quản lý trong giao diện này là mặc định; email/Zalo/Slack chưa bật).
4. Chuẩn dịch vụ (giờ làm, SLA) để thay bản nháp.
