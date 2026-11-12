// Cầu nối Zalo cá nhân (zca-js, KHÔNG CHÍNH THỨC). Giai đoạn 1: CHỈ ĐỌC. Không có mã gửi tin ở đây.
// Lệnh:  node bridge.mjs login | groups | run
import fs from "node:fs";
import path from "node:path";
import { Zalo, ThreadType, LoginQRCallbackEventType } from "zca-js";
import { normalize } from "./normalize.mjs";

const SECRETS = process.env.ZALO_SECRETS_DIR || path.resolve("../../secrets");
const SESSION = path.join(SECRETS, "zalo-session.json");
const URL_BASE = process.env.CAREAI_URL || "http://127.0.0.1:8765";
const TOKEN = process.env.CAREAI_BRIDGE_TOKEN || "";
const ALLOWED = new Set((process.env.ZALO_ALLOWED_GROUPS || "").split(",").map((s) => s.trim()).filter(Boolean));
const log = (...a) => console.log(new Date().toISOString(), ...a);   // KHÔNG log nội dung tin hay cookie

async function login() {
  fs.mkdirSync(SECRETS, { recursive: true, mode: 0o700 });
  const qr = path.join(SECRETS, "zalo-qr.png");
  const api = await new Zalo({}).loginQR({ qrPath: qr }, (ev) => {
    if (ev.type === LoginQRCallbackEventType.QRCodeGenerated) { ev.actions.saveToFile(qr); log("Mở", qr, "và quét bằng app Zalo của TÀI KHOẢN TRỢ LÝ (không dùng tài khoản nhân viên)."); }
    else if (ev.type === LoginQRCallbackEventType.QRCodeScanned) log("Đã quét, hãy xác nhận trên điện thoại.");
    else if (ev.type === LoginQRCallbackEventType.QRCodeExpired) ev.actions.retry();
    else if (ev.type === LoginQRCallbackEventType.QRCodeDeclined) log("Bị từ chối.");
    else if (ev.type === LoginQRCallbackEventType.GotLoginInfo) {
      fs.writeFileSync(SESSION, JSON.stringify({ cookie: ev.data.cookie, imei: ev.data.imei, userAgent: ev.data.userAgent }), { mode: 0o600 });
      log("Đã lưu phiên vào", SESSION, "(không commit, không chia sẻ).");
    }
  });
  log("Đăng nhập xong. Own id:", api.getOwnId());
  process.exit(0);
}

async function connect() {
  if (!fs.existsSync(SESSION)) throw new Error("Chưa có phiên. Chạy: node bridge.mjs login");
  return new Zalo({}).login(JSON.parse(fs.readFileSync(SESSION, "utf8")));
}

async function groups() {   // chế độ khám phá: chỉ in id + tên nhóm, KHÔNG đọc nội dung tin
  const api = await connect();
  const ids = Object.keys((await api.getAllGroups()).gridVerMap);
  const info = (await api.getGroupInfo(ids)).gridInfoMap;
  for (const id of ids) console.log(id, "\t", info[id]?.name);
  process.exit(0);
}

async function post(p, body) {
  const r = await fetch(URL_BASE + p, { method: "POST", headers: { Authorization: "Bearer " + TOKEN, "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(`${p} -> HTTP ${r.status}`);
}

async function run() {
  if (!TOKEN) throw new Error("Thiếu CAREAI_BRIDGE_TOKEN");
  if (!ALLOWED.size) throw new Error("ZALO_ALLOWED_GROUPS rỗng: chạy 'groups' rồi liệt kê nhóm được phép");
  const api = await connect(); const own = api.getOwnId();
  let queue = [], connected = false;
  const beat = (state, detail) => post("/api/bridge/heartbeat", { channel: "zalo", state, detail, own_id: own }).catch((e) => log("heartbeat lỗi:", e.message));
  const flush = async () => {
    if (!queue.length) return;
    const batch = queue.splice(0, 50);
    try { await post("/api/bridge/ingest", { channel: "zalo", messages: batch }); }
    catch (e) { queue.unshift(...batch); log("ingest lỗi, giữ lại", queue.length, "tin để thử lại:", e.message); }   // server khử trùng theo msg_id
  };
  api.listener.on("message", (m) => {
    if (m.threadId == null || !ALLOWED.has(String(m.threadId))) return;     // lớp lọc 1: nhóm lạ bị bỏ ngay trong tiến trình
    const n = normalize(m, own, ThreadType.Group); if (n) queue.push(n);
  });
  api.listener.on("connected", () => { connected = true; beat("ok", "đã kết nối"); log("connected"); });
  api.listener.on("disconnected", (c, r) => { connected = false; beat("down", `ngắt kết nối ${c} ${r}`); log("disconnected", c); });
  api.listener.on("closed", (c, r) => { connected = false; beat("down", `đóng ${c} ${r} (DuplicateConnection=3000: mở Zalo Web ở nơi khác)`); log("closed", c); });
  api.listener.on("error", (e) => log("error", e?.message || e));
  api.listener.start({ retryOnClose: true });
  setInterval(flush, 2000);
  setInterval(() => beat(connected ? "ok" : "down", connected ? "heartbeat" : "chưa kết nối"), 30000);
  log("Bridge chạy, CHỈ ĐỌC, nhóm cho phép:", [...ALLOWED].join(","));
}

const cmd = process.argv[2];
({ login, groups, run }[cmd] || (() => { console.log("Dùng: node bridge.mjs login|groups|run"); process.exit(1); }))().catch((e) => { console.error("LỖI:", e.message); process.exit(1); });
