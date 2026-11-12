import sys, os
from .app import App, serve
if __name__ == "__main__":
    demo = "--demo" in sys.argv
    os.makedirs("data", exist_ok=True)
    app = App(":memory:" if demo else os.environ.get("CAREAI_DB", "data/careai.db"))
    if demo:
        from .demo import seed; seed(app); print("CHẾ ĐỘ DEMO: dữ liệu GIẢ LẬP, lưu trong bộ nhớ.")
    print("Token quản lý (chỉ hiện một lần, không ghi log):", app.mgr)
    serve(app)
