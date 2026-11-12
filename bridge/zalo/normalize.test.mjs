import test from "node:test"; import assert from "node:assert";
import { ThreadType } from "zca-js"; import { normalize } from "./normalize.mjs";
// DỮ LIỆU TỔNG HỢP theo kiểu dữ liệu của zca-js (d.ts) — KHÔNG phải tin thật.
const mk = (data, over = {}) => ({ type: ThreadType.Group, threadId: "G1", isSelf: false, data: { msgId: "5", uidFrom: "u1", dName: "Lan", ts: "1794189600000", content: "chào", msgType: "webchat", ...data }, ...over });
test("nhóm văn bản", () => { const n = normalize(mk({ mentions: [{ uid: "ai" }], quote: { globalMsgId: 9 } }), "ai", ThreadType.Group);
  assert.deepEqual([n.group_ext_id, n.msg_ext_id, n.kind, n.ts, n.mentions, n.reply_to_ext_id], ["G1", "5", "text", 1794189600, ["ai"], "9"]); });
test("bỏ tin 1-1", () => assert.equal(normalize(mk({}, { type: ThreadType.User }), "ai", ThreadType.Group), null));
test("tin của chính tài khoản", () => assert.equal(normalize(mk({ uidFrom: "ai" }), "ai", ThreadType.Group).is_self, true));
test("file/ghi âm không lấy nội dung", () => { const n = normalize(mk({ content: { href: "x" }, msgType: "chat.voice" }), "ai", ThreadType.Group); assert.equal(n.kind, "voice"); assert.equal(n.text, ""); });
