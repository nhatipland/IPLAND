import sys, os
from .app import App, serve
if __name__ == "__main__":
    demo = "--demo" in sys.argv
    os.makedirs("data", exist_ok=True)
    app = App(":memory:" if demo else os.environ.get("CAREAI_DB", "data/careai.db"))
    if demo:
        from .demo import seed; seed(app); print("CHẾ ĐỘ DEMO: dữ liệu GIẢ LẬP, lưu trong bộ nhớ.")
    sf = os.path.join(os.path.dirname(__file__), "..", "..", "config", "style_nhat.md")
    if os.path.exists(sf) and not app.db.q("SELECT 1 FROM style_profiles"):
        app.db.x("INSERT INTO style_profiles(name,body,approved) VALUES(?,?,0)", "Nhất Nguyễn", open(sf, encoding="utf-8").read())
        print("Đã nạp phong cách (CHƯA duyệt): vào tab 'Phong cách' để duyệt.")
    print("Token quản lý (chỉ hiện một lần, không ghi log):", app.mgr)
    serve(app)
