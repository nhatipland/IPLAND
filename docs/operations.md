# Cài đặt, vận hành, bảo mật, chi phí

## Chạy (hiện chỉ chế độ demo/giả lập)
```
pip install pytest          # chỉ để test; lõi chỉ dùng thư viện chuẩn Python 3.11+
cp .env.example .env ; cp config/standards.example.json config/standards.json
cd src && PYTHONPATH=. python3 -m careai --demo      # mở http://127.0.0.1:8765 ; token in ra console một lần
cd .. && python3 -m pytest -q tests
```
Chạy thật (không `--demo`): DB ở `CAREAI_DB`. Chỉ nghe `127.0.0.1`; muốn truy cập từ xa phải đặt sau HTTPS reverse proxy (chưa làm). **Dừng:** nút "DỪNG KHẨN CẤP" (kill switch, lưu DB) hoặc Ctrl+C. **Khôi phục:** khởi động lại; khử trùng theo (nhóm, msg_id) nên tin xử lý lại không bị lặp; bản nháp `send_uncertain` cần người xem nhóm.
Bí mật (token, khóa API, phiên Zalo) chỉ qua biến môi trường/tệp ngoài git (`.gitignore` đã loại `.env`, `secrets/`, `sessions/`). Không dán vào chat; log server không ghi URL/token.

## Bảo mật & dữ liệu (đã làm / chưa làm)
- Đã: token quản lý vs staff (staff chỉ xem nhóm + tạm dừng); nhật ký `audit` cho thay đổi quan trọng; nhóm lạ bị bỏ, không lưu nội dung; tách ngữ cảnh theo nhóm (có test).
- **Chưa làm:** mã hóa DB, chính sách lưu giữ/xóa tự động, sao lưu, đăng nhập theo người dùng, giao diện CSKH/coach riêng, HTTPS. Bảng `consent` đã có để ghi nhận thành viên được thông báo/đồng ý (API `/api/consent`); **nội dung thông báo & cơ sở pháp lý cần bạn/tư vấn pháp lý quyết định** (dữ liệu sức khỏe là dữ liệu nhạy cảm; xem Nghị định 13/2023 — chưa thẩm định ở đây).
- Không dùng dữ liệu khách để huấn luyện mô hình.

## Chi phí AI (công thức, chưa có đơn giá)
`Chi phí/tháng = N_lượt_trả_lời × (T_vào + T_ra) × đơn giá` — **giả định** T_vào≈1.500 token (KB+15 tin), T_ra≈150. Mức ví dụ N: 300 / 3.000 / 30.000 lượt/tháng. Đơn giá: điền theo bảng giá nhà cung cấp hiện hành (chưa kiểm tra). Bảng `ai_usage` + `/api/usage` đã theo dõi số lượt/ký tự.
