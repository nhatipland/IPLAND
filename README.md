# CareAI — trợ lý nhóm chat & giám sát chất lượng chăm sóc

> **Trạng thái trung thực (2026-11-12):** lõi (nhận tin, quyết định trả lời, nháp/duyệt/gửi, giám sát, báo cáo, giao diện) đã viết và **kiểm thử bằng dữ liệu giả lập (30 test Python + 4 test Node đạt)**. **Chưa kết nối Zalo/Messenger thật; chưa đọc/gửi tin thật nào; chưa gọi mô hình AI thật.** Không nên coi đây là hệ thống hoàn thành.

- `docs/feasibility.md` — khả thi Zalo/Messenger + các lựa chọn cần bạn quyết định
- `docs/connect-zalo.md` — cách kết nối Zalo (zca-js, chỉ đọc) + phiếu kiểm chứng; `docs/messenger-vetting.md` — thẩm định thư viện Messenger
- `bridge/zalo/` — cầu nối Zalo (chỉ đọc, chưa đăng nhập thật)
- `docs/architecture.md`, `docs/operations.md` — kiến trúc, vận hành, bảo mật, chi phí
- `src/careai/` — mã; `web/index.html` — giao diện quản lý; `tests/` — kiểm thử; `config/standards.example.json` — chuẩn dịch vụ **bản nháp chưa duyệt**

## Đã kiểm chứng (bằng test giả lập)
Bỏ nhóm ngoài danh sách · khử trùng tin · không trả lời tin không gọi AI/tin của AI · gom tin liên tiếp (debounce) · tiếp nối chỉ khi chắc · tiếp quản/tạm dừng (khách không điều khiển được) · kill switch · chế độ xem trước không gửi · gửi đúng một lần · lỗi gửi không tự gửi lại · giới hạn tần suất · không bịa giá, không nói "đã làm" · chuyển người với câu hỏi sức khỏe · chống chèn lệnh (regex cơ bản) · cô lập ngữ cảnh giữa nhóm · giờ làm việc ICT · AI không tính là nhân viên · im lặng không bị phạt · cam kết quá hạn chỉ là "suy luận" · vai trò chưa biết không bị đoán.

## Giới hạn / chưa kiểm chứng
- Kênh thật: 🟥 chưa. Nhận diện mention/reply trên nền tảng thật: chưa biết.
- Phân tích tiếng Việt dựa **từ khóa/regex** (thô; sẽ nhầm đùa, phủ định phức tạp) — cần bộ đánh giá với dữ liệu thật và so sánh với quản lý (bước F).
- `StubLLM` chỉ trích KB; `AnthropicLLM` viết nhưng **chưa chạy với khóa thật**.
- Ảnh/file/ghi âm: chưa xử lý nội dung. Chưa có: quy trình cải tiến A/B trên bộ tình huống, lịch chăm sóc theo vai trò, xu hướng tuần, gửi báo cáo ra ngoài, UI cho CSKH/coach.

## Bước tiếp theo (ưu tiên)
1. Bạn chọn phương án kết nối + nhóm thử (xem cuối `docs/feasibility.md`). 2. Thử đọc-chỉ cho 1 nhóm/kênh, ghi kết quả vào bảng khả thi. 3. Duyệt chuẩn dịch vụ & KB. 4. Chạy chế độ xem trước, so sánh với đánh giá quản lý. 5. Thử gửi trong nhóm thử. 6. Bảo mật/lưu giữ/đồng ý. 7. Chỉ khi bạn xác nhận: nhóm khách thật.
