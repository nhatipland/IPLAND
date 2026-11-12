# Kiến trúc & luồng dữ liệu

```
 Nhóm Zalo/Messenger ──(Adapter kênh: CHƯA kiểm chứng; hiện chỉ có SimulatedChannel)──┐
                                                                                      ▼
                         Ingest: allowlist → khử trùng (channel,group,msg_id) → bỏ tin của AI → lưu SQLite
                                         │ trigger? (mention / gọi tên / reply AI / tiếp nối chắc chắn)
              ┌──────────────────────────┴───────────────────────────┐
   A. Responder.tick (debounce, rate-limit,         B. Monitor/Reports (đọc-only, giờ làm việc ICT,
      pause/kill) → Draft (KB đã duyệt + guardrail)    bằng chứng + độ chắc chắn, AI ≠ nhân viên)
              │                                                       │
        Outbox (cổng gửi DUY NHẤT: kill, allowed,           Giao diện quản lý (token) / báo cáo
        mode=live, !paused, idempotency) ──► Adapter.send           — không bao giờ đăng vào nhóm
```
- **Dữ liệu gửi nhà cung cấp AI** (chỉ khi `CAREAI_LLM=anthropic`): system prompt, ≤15 tin gần nhất *của đúng nhóm đó*, câu hỏi, đoạn KB đã duyệt. Không gửi dữ liệu nhóm khác/báo cáo. Mặc định `stub` (không gửi gì ra ngoài).
- **Bốn kho tách riêng:** `messages` (ngữ cảnh ngắn hạn) · hồ sơ khách (`groups.customer_code`, `commitments`, `external_facts`, `members`) · `kb_docs`+`kb_versions` (đã duyệt, có phiên bản/rollback) · `improvements` (câu chưa giải quyết).
- **Không tự gộp hồ sơ Zalo/Messenger**: nhóm khóa theo (channel, external_id); không có logic gộp theo tên.
- **Phòng thủ chèn lệnh:** nội dung chat chỉ là dữ liệu; regex phát hiện yêu cầu bỏ quy tắc/lộ dữ liệu → từ chối mẫu; hậu kiểm chặn giá không có trong KB và câu "đã đặt lịch/đã gửi…"; mô hình không có công cụ nào để gửi/đặt lịch.
- **Lỗi gửi mơ hồ** (timeout): trạng thái `send_uncertain`, không tự gửi lại (tránh trùng); cần người kiểm tra.
